import uuid
from datetime import datetime

import pandas as pd
import streamlit as st

from sheets import (
    read_sheet,
    append_row,
    update_balance,
    overwrite_leave_requests
)

st.set_page_config(
    page_title="有給休暇管理アプリ",
    page_icon="🏖️",
    layout="wide"
)

st.title("🏖️ 有給休暇管理アプリ")

menu = st.sidebar.radio(
    "メニュー",
    [
        "ダッシュボード",
        "有給申請",
        "申請一覧",
        "残日数確認",
        "承認管理"
    ]
)

users_df = read_sheet("users")
requests_df = read_sheet("leave_requests")
balance_df = read_sheet("leave_balance")

if menu == "ダッシュボード":

    st.subheader("ダッシュボード")

    employee_count = len(users_df)

    total_granted = 0
    total_used = 0
    total_remaining = 0

    if not balance_df.empty:
        total_granted = balance_df["granted_days"].sum()
        total_used = balance_df["used_days"].sum()
        total_remaining = balance_df["remaining_days"].sum()

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("社員数", employee_count)
    col2.metric("付与日数", total_granted)
    col3.metric("使用日数", total_used)
    col4.metric("残日数", total_remaining)

    st.divider()

    if not balance_df.empty:

        dashboard_df = balance_df.merge(
            users_df[["user_id", "employee_name"]],
            on="user_id",
            how="left"
        )

        st.subheader("残日数一覧")

        chart_df = dashboard_df[
            ["employee_name", "remaining_days"]
        ].set_index("employee_name")

        st.bar_chart(chart_df)

        st.subheader("社員別有給残数")

        st.dataframe(
            dashboard_df[
                [
                    "employee_name",
                    "granted_days",
                    "used_days",
                    "remaining_days"
                ]
            ],
            use_container_width=True
        )

if menu == "有給申請":

    st.subheader("有給申請")

    employee_name = st.selectbox(
        "社員名",
        users_df["employee_name"].tolist()
    )

    start_date = st.date_input("開始日")
    end_date = st.date_input("終了日")

    comment = st.text_area("申請理由")

    if st.button("申請する"):

        request_days = (
            end_date - start_date
        ).days + 1

        user = users_df[
            users_df["employee_name"] == employee_name
        ].iloc[0]

        append_row(
            "leave_requests",
            [
                f"R-{uuid.uuid4().hex[:8]}",
                user["user_id"],
                str(start_date),
                str(end_date),
                request_days,
                "pending",
                comment,
                datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
            ]
        )

        st.success("申請を登録しました")

if menu == "申請一覧":

    st.subheader("申請一覧")

    if not requests_df.empty:

        result_df = requests_df.merge(
            users_df[
                [
                    "user_id",
                    "employee_name"
                ]
            ],
            on="user_id",
            how="left"
        )

        result_df = result_df[
            [
                "request_id",
                "employee_name",
                "start_date",
                "end_date",
                "days",
                "status",
                "comment"
            ]
        ]

        st.dataframe(
            result_df,
            use_container_width=True
        )

    else:
        st.info("申請データなし")

if menu == "残日数確認":

    st.subheader("残日数確認")

    if not balance_df.empty:

        result_df = balance_df.merge(
            users_df[
                [
                    "user_id",
                    "employee_name"
                ]
            ],
            on="user_id",
            how="left"
        )

        st.dataframe(
            result_df[
                [
                    "employee_name",
                    "granted_days",
                    "used_days",
                    "remaining_days"
                ]
            ],
            use_container_width=True
        )

    else:
        st.info("残日数データなし")

if menu == "承認管理":

    st.subheader("承認管理")

    if requests_df.empty:
        st.info("申請データなし")

    else:

        pending_df = requests_df[
            requests_df["status"] == "pending"
        ]

        if pending_df.empty:
            st.success("承認待ち申請はありません")

        for idx, row in pending_df.iterrows():

            employee_name = users_df[
                users_df["user_id"] == row["user_id"]
            ]["employee_name"].iloc[0]

            with st.container():

                st.markdown(
                    f"""
                    #### {employee_name}

                    - 期間：{row['start_date']} ～ {row['end_date']}
                    - 日数：{row['days']}日
                    - 理由：{row['comment']}
                    """
                )

                col1, col2 = st.columns(2)

                with col1:

                    if st.button(
                        "承認",
                        key=f"approve_{idx}"
                    ):

                        requests_df.loc[
                            idx,
                            "status"
                        ] = "approved"

                        overwrite_leave_requests(
                            requests_df
                        )

                        update_balance(
                            row["user_id"]
                        )

                        st.success(
                            "承認しました"
                        )

                        st.rerun()

                with col2:

                    if st.button(
                        "却下",
                        key=f"reject_{idx}"
                    ):

                        requests_df.loc[
                            idx,
                            "status"
                        ] = "rejected"

                        overwrite_leave_requests(
                            requests_df
                        )

                        st.warning(
                            "却下しました"
                        )

                        st.rerun()

                st.divider()
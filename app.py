import uuid
from datetime import datetime

import streamlit as st
import pandas as pd

from sheets import (
    read_sheet,
    append_row,
    update_balance
)

st.set_page_config(
    page_title="有給休暇管理アプリ",
    page_icon="🏖️",
    layout="wide"
)

st.title(
    "🏖️ 有給休暇管理アプリ"
)

menu = st.sidebar.radio(
    "メニュー",
    [
        "ダッシュボード",
        "有給登録",
        "残日数確認"
    ]
)

users_df = read_sheet(
    "users"
)

requests_df = read_sheet(
    "leave_requests"
)

balance_df = read_sheet(
    "leave_balance"
)

# ------------------------------
# ダッシュボード
# ------------------------------

if menu == "ダッシュボード":

    st.subheader(
        "ダッシュボード"
    )

    employee_count = len(
        users_df
    )

    total_granted = 0
    total_used = 0

    if not balance_df.empty:

        total_granted = (
            balance_df[
                "granted_days"
            ].sum()
        )

        total_used = (
            balance_df[
                "used_days"
            ].sum()
        )

    leave_rate = 0

    if total_granted > 0:

        leave_rate = round(
            (
                total_used
                / total_granted
            ) * 100,
            1
        )

    col1, col2 = st.columns(2)

    with col1:

        st.metric(
            "社員数",
            employee_count
        )

    with col2:

        st.metric(
            "有給取得率",
            f"{leave_rate}%"
        )

    st.divider()

    st.subheader(
        "残日数一覧"
    )

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

        result_df = result_df[
            [
                "employee_name",
                "remaining_days"
            ]
        ]

        st.dataframe(
            result_df,
            use_container_width=True
        )

        chart_df = result_df.set_index(
            "employee_name"
        )

        st.bar_chart(
            chart_df
        )

# ------------------------------
# 有給登録
# ------------------------------

elif menu == "有給登録":

    st.subheader(
        "有給登録"
    )

    employee_name = st.selectbox(
        "社員名",
        users_df[
            "employee_name"
        ].tolist()
    )

    leave_type = st.radio(
        "種別",
        [
            "午前半休",
            "午後半休",
            "終日休暇"
        ]
    )

    if st.button(
        "登録する"
    ):

        if leave_type in (
            "午前半休",
            "午後半休"
        ):
            days = 0.5
        else:
            days = 1.0

        user = users_df[
            users_df[
                "employee_name"
            ] == employee_name
        ].iloc[0]

        append_row(
            "leave_requests",
            [
                f"R-{uuid.uuid4().hex[:8]}",
                user["user_id"],
                leave_type,
                days,
                datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
            ]
        )

        update_balance(
            user["user_id"]
        )

        st.success(
            "有給を登録しました"
        )

# ------------------------------
# 残日数確認
# ------------------------------

elif menu == "残日数確認":

    st.subheader(
        "残日数確認"
    )

    if balance_df.empty:

        st.info(
            "データがありません"
        )

    else:

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

        result_df = result_df[
            [
                "employee_name",
                "granted_days",
                "used_days",
                "remaining_days"
            ]
        ]

        st.dataframe(
            result_df,
            use_container_width=True
        )
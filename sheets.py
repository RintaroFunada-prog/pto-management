import pandas as pd
import gspread
import streamlit as st

from google.oauth2.service_account import Credentials

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

SPREADSHEET_NAME = (
    "Paid_Time_Off_Manegement"
)


def get_client():

    credentials = (
        Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=SCOPES
        )
    )

    return gspread.authorize(
        credentials
    )


def get_spreadsheet():

    client = get_client()

    return client.open(
        SPREADSHEET_NAME
    )


def read_sheet(sheet_name):

    sheet = (
        get_spreadsheet()
        .worksheet(sheet_name)
    )

    records = sheet.get_all_records()

    if not records:
        return pd.DataFrame()

    return pd.DataFrame(records)


def append_row(sheet_name, row):

    sheet = (
        get_spreadsheet()
        .worksheet(sheet_name)
    )

    sheet.append_row(row)


def overwrite_leave_requests(df):

    sheet = (
        get_spreadsheet()
        .worksheet("leave_requests")
    )

    sheet.clear()

    data = [
        df.columns.tolist()
    ] + df.values.tolist()

    sheet.update(data)


def update_balance(user_id):

    users_df = read_sheet("users")

    requests_df = read_sheet(
        "leave_requests"
    )

    user = users_df[
        users_df["user_id"] == user_id
    ]

    if user.empty:
        return

    granted_days = float(
        user.iloc[0][
            "annual_grant_days"
        ]
    )

    approved = requests_df[
        (requests_df["user_id"] == user_id)
        &
        (
            requests_df["status"]
            == "approved"
        )
    ]

    used_days = approved["days"].sum()

    remaining_days = (
        granted_days - used_days
    )

    balance_sheet = (
        get_spreadsheet()
        .worksheet("leave_balance")
    )

    records = (
        balance_sheet
        .get_all_records()
    )

    found = False

    for i, record in enumerate(
        records,
        start=2
    ):

        if record["user_id"] == user_id:

            balance_sheet.update(
                f"A{i}:E{i}",
                [[
                    user_id,
                    granted_days,
                    used_days,
                    remaining_days,
                    pd.Timestamp.now().strftime(
                        "%Y-%m-%d"
                    )
                ]]
            )

            found = True

            break

    if not found:

        balance_sheet.append_row(
            [
                user_id,
                granted_days,
                used_days,
                remaining_days,
                pd.Timestamp.now().strftime(
                    "%Y-%m-%d"
                )
            ]
        )
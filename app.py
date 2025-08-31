import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

st.title("Google Sheets 接続テスト")

def get_worksheet():
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )
    client = gspread.authorize(creds)
    SPREADSHEET_ID = "1x_s58xCJco6c-mAC5AiwVf_Jg0XJb1mImaIcwXlXKvI"
    sheet = client.open_by_key(SPREADSHEET_ID).sheet1
    return sheet

try:
    sheet = get_worksheet()
    sheet.append_row(["TEST", "0000000", "テスト単語", "接続OK"])
    st.success("✅ 書き込み成功！")
except Exception as e:
    st.error(f"❌ 書き込み失敗: {e}")

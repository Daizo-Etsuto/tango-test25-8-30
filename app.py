import random
import pandas as pd
import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

st.title("英単語テスト（CSV版・学習ログ付き）")

# ==== Google Sheets に接続 ====
def get_worksheet():
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )
    client = gspread.authorize(creds)
    SPREADSHEET_ID = "1x_s58xCJco6c-mAC5AiwVf_Jg0XJb1mImaIcwXlXKvI"
    sheet = client.open_by_key(SPREADSHEET_ID).sheet1
    return sheet   # 👈 ← インデントを関数内に揃える


# ==== 接続テスト ====
try:
    sheet = get_worksheet()
    sheet.append_row(["TEST", "0000000", "テスト単語", "接続OK"])
    st.info("✅ Google Sheets 書き込みテスト：成功しました！")
except Exception as e:
    st.error(f"❌ Google Sheets 書き込みテスト：失敗しました。エラー：{e}")


    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )
    client = gspread.authorize(creds)
    SPREADSHEET_ID = "1x_s58xCJco6c-mAC5AiwVf_Jg0XJb1mImaIcwXlXKvI"  # ← EtsutoさんのシートID
    sheet = client.open_by_key(SPREADSHEET_ID).sheet1
    return sheet

def log_result(student_id, word, result):
    sheet = get_worksheet()
    sheet.append_row([
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        str(student_id),
        word,
        result
    ])

# ==== 生徒番号入力 ====
student_id = st.number_input("生徒番号（7ケタ）を入力してください", min_value=1000000, max_value=9999999, step=1)
if not student_id:
    st.stop()

# ==== 単語リストアップロード ====
uploaded_file = st.file_uploader("単語リスト（CSV, UTF-8推奨）をアップロードしてください", type=["csv"])
if uploaded_file is None:
    st.info("まずは CSV をアップロードしてください。")
    st.stop()

# ==== CSV読み込み ====
try:
    df = pd.read_csv(uploaded_file, encoding="utf-8")
except UnicodeDecodeError:
    df = pd.read_csv(uploaded_file, encoding="shift-jis")

if not {"単語", "意味"}.issubset(df.columns):
    st.error("CSVには『単語』『意味』列が必要です。")
    st.stop()

# ==== セッション初期化 ====
ss = st.session_state
if "remaining" not in ss: ss.remaining = df.to_dict("records")
if "current" not in ss: ss.current = None
if "phase" not in ss: ss.phase = "quiz"
if "last_outcome" not in ss: ss.last_outcome = None

def next_question():
    if not ss.remaining:
        ss.current = None
        ss.phase = "done"
        return
    ss.current = random.choice(ss.remaining)
    ss.phase = "quiz"
    ss.last_outcome = None

def check_answer(ans: str) -> bool:
    word = ss.current["単語"]
    return word.lower().startswith(ans.strip().lower())

# ==== 全問終了 ====
if ss.phase == "done":
    st.success("全問正解！お疲れさまでした🎉")
    st.stop()

# ==== 新しい問題 ====
if ss.current is None and ss.phase == "quiz":
    next_question()

# ==== 出題 ====
if ss.phase == "quiz" and ss.current:
    current = ss.current
    st.subheader(f"意味: {current['意味']}")

    with st.form("answer_form", clear_on_submit=True):
        ans = st.text_input("最初の2文字を入力（半角英数字）", max_chars=2, key="answer_box")
        submitted = st.form_submit_button("解答（Enter）")

    # 自動フォーカス
    components.html(
        """
        <script>
        const box = window.parent.document.querySelector('input[type="text"]');
        if (box) { box.focus(); box.select(); }
        </script>
        """,
        height=0,
    )

    if submitted and ans and len(ans.strip()) == 2 and ans.isascii():
        if check_answer(ans):
            ss.remaining = [q for q in ss.remaining if q != current]
            ss.last_outcome = ("correct", current["単語"])
        else:
            ss.last_outcome = ("wrong", current["単語"])
        ss.phase = "feedback"
        st.rerun()

# ==== フィードバック ====
if ss.phase == "feedback" and ss.last_outcome:
    status, word = ss.last_outcome
    if status == "correct":
        st.markdown(f"<div style='background:#e6ffe6;padding:6px;'>正解！ {word} 🎉</div>", unsafe_allow_html=True)
        log_result(student_id, word, "正解")
    elif status == "wrong":
        st.markdown(f"<div style='background:#ffe6e6;padding:6px;'>不正解！ 正解は {word}</div>", unsafe_allow_html=True)
        log_result(student_id, word, "不正解")
    elif status == "timeout":
        st.markdown(f"<div style='background:#ffe6e6;padding:6px;'>時間切れ！ 正解は {word}</div>", unsafe_allow_html=True)
        log_result(student_id, word, "時間切れ")

    st.write("下のボタンを押すか、Tabを押してからリターンを押してください。")

    if st.button("次の問題へ"):
        next_question()
        st.rerun()





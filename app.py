import time
import random
import pandas as pd
import streamlit as st

st.title("英単語テスト（CSV版・安定版）")

uploaded_file = st.file_uploader("単語リスト（CSV, UTF-8推奨）をアップロードしてください", type=["csv"])
if uploaded_file is None:
    st.info("まずは CSV をアップロードしてください。")
    st.stop()

# CSV読み込み
try:
    df = pd.read_csv(uploaded_file, encoding="utf-8")
except UnicodeDecodeError:
    df = pd.read_csv(uploaded_file, encoding="shift-jis")

# 必須列チェック
if not {"単語", "意味"}.issubset(df.columns):
    st.error("CSVには『単語』『意味』列が必要です。")
    st.stop()

# ==== セッション初期化 ====
ss = st.session_state
defaults = {
    "remaining": df.to_dict("records"),
    "current": None,
    "phase": "quiz",      # "quiz" / "feedback" / "done"
    "start_time": None,
    "hint": "",
    "last_outcome": None,
}
for k, v in defaults.items():
    if k not in ss:
        ss[k] = v

def next_question():
    if not ss.remaining:
        ss.current = None
        ss.ph

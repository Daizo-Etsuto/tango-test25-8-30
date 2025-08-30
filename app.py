import time
import random
import pandas as pd
import streamlit as st
from streamlit_autorefresh import st_autorefresh  # ← モジュール名はこれでOK

# 1秒ごとに再描画（無制限）
st_autorefresh(interval=1000, limit=0, key="tick")

st.title("英単語テスト（CSV版・自動ヒント付き）")

uploaded_file = st.file_uploader("単語リスト（CSV, UTF-8推奨）をアップロードしてください", type=["csv"])

if uploaded_file is None:
    st.info("まずは CSV をアップロードしてください。")
    st.stop()

# CSV読み込み
try:
    df = pd.read_csv(uploaded_file, encoding="utf-8")
except UnicodeDecodeError:
    df = pd.read_csv(uploaded_file, encoding="shift-jis")

# 必須列確認
if not {"単語", "意味"}.issubset(df.columns):
    st.error("CSVには『単語』『意味』の2列（ヘッダー名そのまま）が必要です。")
    st.stop()

# セッション初期化
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
    """次の問題へ"""
    if not ss.remaining:
        ss.current = None
        ss.phase = "done"
        return
    ss.current = random.choice(ss.remaining)
    ss.phase = "quiz"
    ss.start_time = time.time()
    ss.hint = ""
    ss.last_outcome = None

def check_answer(ans: str) -> bool:
    word = ss.current["単語"]
    return word.lower().startswith(ans.strip().lower())

# 終了ボタン
if st.button("終了する"):
    st.write("テストを終了しました。")
    st.stop()

# 全問完了
if ss.phase == "done":
    st.success("全問正解！お疲れさまでした🎉")
    st.stop()

# 問題セット
if ss.current is None and ss.phase == "quiz":
    next_question()

# 出題フェーズ
if ss.phase == "quiz" and ss.current:
    current = ss.current
    st.subheader(f"意味: {current['意味']}")

    # 解答フォーム（Enterで送信）
    with st.form("quiz_form", clear_on_submit=True):
        ans = st.text_input("最初の2文字を入力（半角英数字）", max_chars=2)
        c1, c2 = st.columns(2)
        submit = c1.form_submit_button("回答（Enter可）")
        skip   = c2.form_submit_button("スキップ")

    if submit and ans:
        if ans.isascii() and len(ans.strip()) == 2:
            if check_answer(ans):
                ss.remaining = [q for q in ss.remaining if q != current]
                ss.last_outcome = ("correct", current["単語"])
            else:
                ss.last_outcome = ("wrong", current["単語"])
            ss.phase = "feedback"
        else:
            st.warning("半角英数字2文字で入力してください。")

    if skip:
        ss.last_outcome = ("skip", current["単語"])
        ss.phase = "feedback"

    # 時間経過（自動更新で毎秒チェック）
    elapsed = time.time() - ss.start_time if ss.start_time else 0
    if elapsed >= 5 and not ss.hint:
        ss.hint = current["単語"][0]
    if ss.hint:
        st.info(f"ヒント: {ss.hint}")
    if elapsed >= 15 and ss.phase == "quiz":
        ss.last_outcome = ("timeout", current["単語"])
        ss.phase = "feedback"

# フィードバックフェーズ
if ss.phase == "feedback" and ss.last_outcome:
    status, word = ss.last_outcome
    if status == "correct":
        st.success(f"正解！ {word} 🎉")
    elif status == "wrong":
        st.error(f"不正解！正解は {word}")
    elif status == "skip":
        st.info(f"スキップしました。正解は {word}")
    elif status == "timeout":
        st.error(f"時間切れ！正解は {word}")

    with st.form("next_form", clear_on_submit=True):
        nxt = st.text_input("Enterで次の問題へ", value="")
        go = st.form_submit_button("次の問題へ（Enter可）")
    if go:
        ss.current = None
        ss.phase = "quiz"
        ss.hint = ""
        ss.last_outcome = None

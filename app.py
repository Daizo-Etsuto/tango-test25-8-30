import time
import random
import pandas as pd
import streamlit as st
from streamlit_autorefresh import st_autorefresh  # ✅ 自動更新

# 1秒ごとに自動再描画
st_autorefresh(interval=1000, key="tick")

st.title("英単語テスト（CSV版・自動ヒント＋Tab→Enter対応）")

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

    ans = st.text_input("最初の2文字を入力（半角英数字）", max_chars=2, key="answer_box")

    if ans and len(ans.strip()) == 2 and ans.isascii():
        if check_answer(ans):
            ss.remaining = [q for q in ss.remaining if q != current]
            ss.last_outcome = ("correct", current["単語"])
        else:
            ss.last_outcome = ("wrong", current["単語"])
        ss.phase = "feedback"

    # 時間制御（自動リフレッシュで毎秒チェック）
    elapsed = time.time() - ss.start_time if ss.start_time else 0
    if elapsed >= 5 and not ss.hint:
        ss.hint = current["単語"][0]
    if ss.hint:
        st.markdown(f"<p style='margin:2px 0;color:#444;'>ヒント: {ss.hint}</p>", unsafe_allow_html=True)
    if elapsed >= 15 and ss.phase == "quiz":
        ss.last_outcome = ("timeout", current["単語"])
        ss.phase = "feedback"

# ==== フィードバック ====
if ss.phase == "feedback" and ss.last_outcome:
    status, word = ss.last_outcome

    # ✅ HTMLでコンパクト表示
    if status == "correct":
        st.markdown(f"<div style='background:#e6ffe6;padding:6px;margin:2px 0;border-radius:6px;'>正解！ {word} 🎉</div>", unsafe_allow_html=True)
    elif status == "wrong":
        st.markdown(f"<div style='background:#ffe6e6;padding:6px;margin:2px 0;border-radius:6px;'>不正解！ 正解は {word}</div>", unsafe_allow_html=True)
    elif status == "timeout":
        st.markdown(f"<div style='background:#ffe6e6;padding:6px;margin:2px 0;border-radius:6px;'>時間切れ！ 正解は {word}</div>", unsafe_allow_html=True)

    # ✅ 案内文を変更
    st.write("下のボタンを押すか、Tabを押してからリターンを押してください。")

    # ボタンを下に配置（Tab1回でここにフォーカスする）
    if st.button("次の問題へ"):
        ss.current = None
        ss.phase = "quiz"
        ss.hint = ""
        ss.last_outcome = None

# ==== 終了ボタン（最後に配置） ====
if st.button("終了する"):
    st.write("テストを終了しました。")
    st.stop()

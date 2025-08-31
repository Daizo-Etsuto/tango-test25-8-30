import random
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

st.title("英単語テスト（CSV版・安定版）")

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
if "phase" not in ss: ss.phase = "quiz"   # quiz / feedback / done
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

# ==== 新しい問題 ====
elif ss.current is None and ss.phase == "quiz":
    next_question()

# ==== 出題 ====
if ss.phase == "quiz" and ss.current:
    current = ss.current
    st.subheader(f"意味: {current['意味']}")

    with st.form("answer_form", clear_on_submit=True):
        ans = st.text_input("最初の2文字を入力（半角英数字）", max_chars=2, key="answer_box")
        submitted = st.form_submit_button("解答（Enter）")

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
        st.markdown(
            f"<div style='background:#e6ffe6;padding:6px;margin:2px 0;border-radius:6px;'>正解！ {word} 🎉</div>",
            unsafe_allow_html=True,
        )
    elif status == "wrong":
        st.markdown(
            f"<div style='background:#ffe6e6;padding:6px;margin:2px 0;border-radius:6px;'>不正解！ 正解は {word}</div>",
            unsafe_allow_html=True,
        )

    st.write("下のボタンを押すか、Tabを押してからリターンを押してください。")

    if st.button("次の問題へ"):
        next_question()
        st.rerun()

# ==== ✅ 画面下に固定された終了ボタン（青系・本当に終了できる） ====
st.markdown(
    """
    <style>
    .close-btn-container {
        position: fixed;
        bottom: 10px;
        left: 0;
        width: 100%;
        text-align: center;
        background: white;
        padding: 10px;
        border-top: 1px solid #ccc;
        z-index: 1000;
    }
    .close-btn-container button {
        background: #2b6cb0 !important;
        color: white !important;
        padding: 10px 20px !important;
        border: none !important;
        border-radius: 8px !important;
        font-size: 16px !important;
        cursor: pointer !important;
    }
    .close-btn-container button:hover {
        background: #1e4e8c !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# container に st.button を入れる
with st.container():
    st.markdown('<div class="close-btn-container">', unsafe_allow_html=True)
    if st.button("アプリを閉じる"):
        st.stop()
    st.markdown('</div>', unsafe_allow_html=True)

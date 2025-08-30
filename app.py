import time
import random
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

st.title("英単語テスト（CSV版・キーボード操作＋自動フォーカス）")

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
    st.error("CSVには『単語』『意味』の列が必要です。")
    st.stop()

# ===== セッション初期化 =====
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

# ===== 終了ボタン =====
if st.button("終了する"):
    st.write("テストを終了しました。")
    st.stop()

# ===== 全問終了 =====
if ss.phase == "done":
    st.success("全問正解！お疲れさまでした🎉")
    st.stop()

# ===== 新しい問題の用意 =====
if ss.current is None and ss.phase == "quiz":
    next_question()

# ===== 出題 =====
if ss.phase == "quiz" and ss.current:
    current = ss.current
    st.subheader(f"意味: {current['意味']}")

    # 解答欄（2文字・半角英数字）
    # NOTE: ラベル文言はフォーカス用JSが参照するので変更しないでください
    ans = st.text_input("最初の2文字を入力（半角英数字）", max_chars=2, key="answer_box")

    # ---- 自動フォーカス（堅牢版：複数セレクタ＆リトライ）----
    components.html(
        """
        <script>
        (function focusAnswer(){
          const tryFocus = () => {
            // 1) ラベル一致で探索
            const labels = window.parent.document.querySelectorAll('label');
            for (const lb of labels) {
              if (lb.innerText && lb.innerText.trim().includes("最初の2文字を入力（半角英数字）")) {
                const inp = lb.parentElement.querySelector('input');
                if (inp) { inp.focus(); inp.select(); return true; }
              }
            }
            // 2) data-testid を使って TextInput 内の input を探索
            const cand = window.parent.document.querySelectorAll('[data-testid="stTextInput"] input');
            for (const el of cand) {
              const aria = el.getAttribute('aria-label') || '';
              if (aria.includes("最初の2文字を入力（半角英数字）")) {
                el.focus(); el.select(); return true;
              }
            }
            // 3) maxlength=2 の input から推定（ページ内で唯一想定）
            const two = window.parent.document.querySelector('input[maxlength="2"]');
            if (two) { two.focus(); two.select(); return true; }
            return false;
          };
          // 初回＋遅延で数回リトライ（描画タイミング差異対策）
          setTimeout(tryFocus, 0);
          setTimeout(tryFocus, 120);
          setTimeout(tryFocus, 300);
          setTimeout(tryFocus, 600);
        })();
        </script>
        """,
        height=0, scrolling=False
    )

    # 回答確定（Enterで送信）
    if ans and len(ans.strip()) == 2 and ans.isascii():
        if check_answer(ans):
            ss.remaining = [q for q in ss.remaining if q != current]
            ss.last_outcome = ("correct", current["単語"])
        else:
            ss.last_outcome = ("wrong", current["単語"])
        ss.phase = "feedback"

    # 時間経過チェック（※完全自動にしたい場合は後述オプション参照）
    elapsed = time.time() - ss.start_time if ss.start_time else 0
    if elapsed >= 5 and not ss.hint:
        ss.hint = current["単語"][0]
    if ss.hint:
        st.info(f"ヒント: {ss.hint}")
    if elapsed >= 15 and ss.phase == "quiz":
        ss.last_outcome = ("timeout", current["単語"])
        ss.phase = "feedback"

# ===== フィードバック =====
if ss.phase == "feedback" and ss.last_outcome:
    status, word = ss.last_outcome
    if status == "correct":
        st.success(f"正解！ {word} 🎉")
    elif status == "wrong":
        st.error(f"不正解！正解は {word}")
    elif status == "timeout":
        st.error(f"時間切れ！正解は {word}")

    st.write("次へ進むには Space（ボタンにフォーカス）または下のボタンを押してください。")
    if st.button("次の問題へ"):
        ss.current = None
        ss.phase = "quiz"
        ss.hint = ""
        ss.last_outcome = None

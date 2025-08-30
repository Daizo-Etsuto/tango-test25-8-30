import streamlit as st
import pandas as pd
import random
import time

st.title("英単語テスト（CSV版・安定動作）")

uploaded_file = st.file_uploader(
    "単語リスト（CSV, UTF-8形式推奨）をアップロードしてください",
    type=["csv"]
)

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file, encoding="utf-8")
    except UnicodeDecodeError:
        df = pd.read_csv(uploaded_file, encoding="shift-jis")

    # 必須カラム確認
    if not {"単語", "意味"}.issubset(df.columns):
        st.error("CSVに『単語』『意味』のヘッダーが必要です。例：単語,意味")
        st.stop()

    # --------------------
    # セッション初期化
    # --------------------
    ss = st.session_state
    if "remaining" not in ss:
        ss.remaining = df.to_dict("records")
    if "current" not in ss:
        ss.current = None
    if "phase" not in ss:
        ss.phase = "quiz"      # "quiz" / "feedback" / "done"
    if "start_time" not in ss:
        ss.start_time = None
    if "hint" not in ss:
        ss.hint = ""
    if "last_outcome" not in ss:
        ss.last_outcome = None

    # --------------------
    # 関数
    # --------------------
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
        """最初の2文字一致で正解判定"""
        word = ss.current["単語"]
        return word.lower().startswith(ans.strip().lower())

    # --------------------
    # 終了ボタン
    # --------------------
    if st.button("終了する"):
        st.write("テストを終了しました。")
        st.stop()

    # --------------------
    # 全問完了チェック
    # --------------------
    if ss.phase == "done":
        st.success("全問正解！お疲れさまでした🎉")
        st.stop()

    if ss.current is None and ss.phase == "quiz":
        next_question()

    # --------------------
    # 出題画面
    # --------------------
    if ss.phase == "quiz" and ss.current:
        current = ss.current
        st.subheader(f"意味: {current['意味']}")

        # 入力欄（2文字, 半角英数字のみ, 小さな幅）
        user_input = st.text_input(
            "最初の2文字を入力してください",
            key="answer_input",
            max_chars=2,
            label_visibility="visible"
        )

        # 入力制限（半角英数字）
        if user_input and not user_input.isascii():
            st.warning("⚠ 半角英数字で入力してください")

        # 回答判定
        if user_input and user_input.isascii():
            if check_answer(user_input):
                ss.remaining = [q for q in ss.remaining if q != current]
                ss.last_outcome = ("correct", current["単語"])
            else:
                ss.last_outcome = ("wrong", current["単語"])
            ss.phase = "feedback"

        # スキップ
        if st.button("スキップ"):
            ss.last_outcome = ("skip", current["単語"])
            ss.phase = "feedback"

        # 時間制御
        elapsed = time.time() - ss.start_time
        if elapsed >= 5 and not ss.hint:
            ss.hint = current['単語'][0]
        if ss.hint:
            st.info(f"ヒント: {ss.hint}")
        if elapsed >= 10:
            ss.last_outcome = ("timeout", current["単語"])
            ss.phase = "feedback"

    # --------------------
    # フィードバック画面
    # --------------------
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

        # 次の問題へ進む
        if st.button("次の問題へ"):
            ss.current = None
            ss.phase = "quiz"
            ss.hint = ""
            ss.last_outcome = None

else:
    st.info("まずは単語リスト（CSV, UTF-8形式）をアップロードしてください。")

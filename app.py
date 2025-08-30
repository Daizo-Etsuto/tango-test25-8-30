import streamlit as st
import pandas as pd
import random
import time

st.title("英単語テスト（CSV版）")
st.write("意味を見て、単語の最初の2文字を入力してください。")

uploaded_file = st.file_uploader("単語リスト（CSV, UTF-8形式推奨）をアップロードしてください", type=["csv"])

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file, encoding="utf-8")
    except UnicodeDecodeError:
        df = pd.read_csv(uploaded_file, encoding="shift-jis")

    # --- セッション初期化 ---
    if "remaining" not in st.session_state:
        st.session_state.remaining = df.to_dict("records")
    if "current" not in st.session_state:
        st.session_state.current = None
    if "start_time" not in st.session_state:
        st.session_state.start_time = None
    if "hint" not in st.session_state:
        st.session_state.hint = ""
    if "answer" not in st.session_state:
        st.session_state.answer = ""
    if "message" not in st.session_state:
        st.session_state.message = None   # 判定メッセージ用フラグ

    def next_question():
        """次の問題を選択"""
        if not st.session_state.remaining:
            st.session_state.current = None
            return
        st.session_state.current = random.choice(st.session_state.remaining)
        st.session_state.start_time = time.time()
        st.session_state.hint = ""
        st.session_state.answer = ""
        st.session_state.message = None

    def check_answer(ans):
        word = st.session_state.current["単語"]
        return word.lower().startswith(ans.strip().lower())

    if st.button("終了する"):
        st.write("テストを終了しました。")
        st.stop()

    if st.session_state.current is None:
        if st.session_state.remaining:
            next_question()
        else:
            st.success("全問正解！お疲れさまでした🎉")
            st.stop()

    current = st.session_state.current
    st.subheader(f"意味: {current['意味']}")

    # 入力欄
    answer = st.text_input(
        "単語の最初の2文字を入力してください（半角英数字のみ）",
        value=st.session_state.answer,
        key="answer_input"
    )

    # 判定処理
    if answer:
        if not answer.isascii():
            st.warning("⚠ 半角英数字で入力してください")
        else:
            if check_answer(answer):
                st.session_state.message = ("correct", current['単語'])
                st.session_state.remaining = [
                    q for q in st.session_state.remaining if q != current
                ]
            else:
                st.session_state.message = ("wrong", current['単語'])
        st.session_state.answer = ""

    # スキップ処理
    if st.button("スキップ"):
        st.session_state.message = ("skip", current['単語'])
        st.session_state.answer = ""

    # 判定メッセージ表示と次の問題処理
    if st.session_state.message:
        status, word = st.session_state.message
        if status == "correct":
            st.success(f"正解！ {word} 🎉")
        elif status == "wrong":
            st.error(f"不正解！正解は {word} です。")
        elif status == "skip":
            st.info(f"スキップしました。正解は {word} です。")

        # 1秒後に次の問題へ
        time.sleep(1)
        st.session_state.current = None
        st.session_state.message = None
        st.rerun()

    # 時間制御
    elapsed = time.time() - st.session_state.start_time

    if elapsed >= 5 and not st.session_state.hint and not st.session_state.message:
        st.session_state.hint = current['単語'][0]

    if st.session_state.hint:
        st.info(f"ヒント: {st.session_state.hint}")

    if elapsed >= 10 and not st.session_state.message:
        st.error(f"時間切れ！正解は {current['単語']} です。")
        st.session_state.current = None
        st.session_state.answer = ""
        st.session_state.message = None
        st.rerun()

else:
    st.info("まずは単語リスト（CSVファイル, UTF-8形式）をアップロードしてください。")

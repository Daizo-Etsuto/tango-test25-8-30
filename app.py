import streamlit as st
import pandas as pd
import random
import time

# --------------------
# タイトル
# --------------------
st.title("英単語テスト（CSV版）")
st.write("意味を見て、単語の最初の2文字を入力してください。")

# --------------------
# ファイルアップロード（CSV専用）
# --------------------
uploaded_file = st.file_uploader("単語リスト（CSV, UTF-8形式推奨）をアップロードしてください", type=["csv"])

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file, encoding="utf-8")
    except UnicodeDecodeError:
        df = pd.read_csv(uploaded_file, encoding="shift-jis")

    # --------------------
    # セッション初期化
    # --------------------
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

    # --------------------
    # 関数
    # --------------------
    def next_question():
        """次の問題を選択"""
        if not st.session_state.remaining:
            st.session_state.current = None
            return
        st.session_state.current = random.choice(st.session_state.remaining)
        st.session_state.start_time = time.time()
        st.session_state.hint = ""
        st.session_state.answer = ""  # 入力リセット

    def check_answer(ans):
        """入力が正解か判定（最初の2文字でOK）"""
        word = st.session_state.current["単語"]
        return word.lower().startswith(ans.strip().lower())

    # --------------------
    # 終了ボタン
    # --------------------
    if st.button("終了する"):
        st.write("テストを終了しました。")
        st.stop()

    # --------------------
    # 出題処理
    # --------------------
    if st.session_state.current is None:
        if st.session_state.remaining:
            next_question()
        else:
            st.success("全問正解！お疲れさまでした🎉")
            st.stop()

    current = st.session_state.current
    st.subheader(f"意味: {current['意味']}")

    # --------------------
    # 回答入力（半角英数字制限）
    # --------------------
    answer = st.text_input(
        "単語の最初の2文字を入力してください（半角英数字のみ）",
        value=st.session_state.answer,
        key="answer_input"
    )

    if answer:
        if not answer.isascii():
            st.warning("⚠ 半角英数字で入力してください")
        else:
            if check_answer(answer):
                # ✅ 正解処理
                st.success(f"正解！ {current['単語']} 🎉")
                st.session_state.remaining = [
                    q for q in st.session_state.remaining if q != current
                ]
                st.session_state.current = None
                st.session_state.answer = ""
                st.rerun()
            else:
                # ❌ 不正解処理（再入力なし → 正解表示して次へ）
                st.error(f"不正解！正解は {current['単語']} です。")
                st.session_state.current = None
                st.session_state.answer = ""
                st.rerun()

    # --------------------
    # スキップ機能
    # --------------------
    if st.button("スキップ"):
        st.info(f"スキップしました。正解は {current['単語']} です。")
        st.session_state.current = None
        st.session_state.answer = ""
        st.rerun()

    # --------------------
    # 時間制御（5秒でヒント, 10秒で答え表示）
    # --------------------
    elapsed = time.time() - st.session_state.start_time

    if elapsed >= 5 and not st.session_state.hint:
        st.session_state.hint = current['単語'][0]

    if st.session_state.hint:
        st.info(f"ヒント: {st.session_state.hint}")

    if elapsed >= 10:
        st.error(f"時間切れ！正解は {current['単語']} です。")
        st.session_state.current = None
        st.session_state.answer = ""
        st.rerun()

else:
    st.info("まずは単語リスト（CSVファイル, UTF-8形式）をアップロードしてください。")

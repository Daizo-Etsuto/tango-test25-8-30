import streamlit as st
import pandas as pd
import random
import time

# --------------------
# タイトル
# --------------------
st.title("英単語テスト")
st.write("意味を見て、単語のスペルを入力してください。")

# --------------------
# ファイルアップロード（Excel or CSV）
# --------------------
uploaded_file = st.file_uploader("単語リスト（Excel または CSV）をアップロードしてください", type=["xlsx", "csv"])

if uploaded_file is not None:
    # Excel or CSV の読み込み
    if uploaded_file.name.endswith(".xlsx"):
        df = pd.read_excel(uploaded_file, sheet_name=0)
    elif uploaded_file.name.endswith(".csv"):
        try:
            df = pd.read_csv(uploaded_file, encoding="utf-8")
        except UnicodeDecodeError:
            # 万が一のため Shift-JIS にも対応
            df = pd.read_csv(uploaded_file, encoding="shift-jis")
    else:
        st.error("対応しているファイル形式は .xlsx または .csv です。")
        st.stop()

    # --------------------
    # セッション状態の初期化
    # --------------------
    if "remaining" not in st.session_state:
        st.session_state.remaining = df.to_dict("records")  # 残っている問題
    if "current" not in st.session_state:
        st.session_state.current = None
    if "start_time" not in st.session_state:
        st.session_state.start_time = None
    if "hint" not in st.session_state:
        st.session_state.hint = ""

    # --------------------
    # 関数定義
    # --------------------
    def next_question():
        """次の問題を選択"""
        if not st.session_state.remaining:
            st.session_state.current = None
            return
        st.session_state.current = random.choice(st.session_state.remaining)
        st.session_state.start_time = time.time()
        st.session_state.hint = ""

    def check_answer(ans):
        """入力が正解か判定"""
        word = st.session_state.current["単語"]
        return ans.strip().lower() == word.lower()

    def give_hint():
        """ヒント（最初の1文字）を表示"""
        word = st.session_state.current["単語"]
        st.session_state.hint = word[0]

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
    # 回答入力
    # --------------------
    answer = st.text_input("単語を入力してください (最初の2文字を含めて)", "")

    if answer:
        if check_answer(answer):
            st.success("正解！🎉")
            # 正解した単語をリストから削除
            st.session_state.remaining = [
                q for q in st.session_state.remaining if q != current
            ]
            st.session_state.current = None
            st.experimental_rerun()
        else:
            st.warning("不正解です。もう一度入力してください。")

    # --------------------
    # 時間制御（5秒後にヒント確認、10秒で解答表示）
    # --------------------
    elapsed = time.time() - st.session_state.start_time

    if 5 <= elapsed < 10 and not st.session_state.hint:
        if st.button("ヒントが欲しいですか？"):
            give_hint()

    if st.session_state.hint:
        st.info(f"ヒント: {st.session_state.hint}")

    if elapsed >= 10:
        st.error(f"時間切れ！正解は {current['単語']} です。")
        # 不正解の問題は残す
        st.session_state.current = None
        st.experimental_rerun()

else:
    st.info("まずは単語リスト（Excel または CSVファイル）をアップロードしてください。")

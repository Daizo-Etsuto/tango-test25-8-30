import streamlit as st
import pandas as pd
import random
import time

# =========================
# 基本設定
# =========================
st.title("英単語テスト（CSV版・安定動作）")
st.write("意味を見て、単語の最初の2文字（半角英数字）を入力してください。")

uploaded_file = st.file_uploader(
    "単語リスト（CSV, UTF-8形式推奨）をアップロードしてください",
    type=["csv"]
)

# =========================
# CSV 読み込み
# =========================
if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file, encoding="utf-8")
    except UnicodeDecodeError:
        # まれにShift-JISのCSVが混ざることがあるため保険
        df = pd.read_csv(uploaded_file, encoding="shift-jis")

    # 必須カラムの存在チェック
    required_cols = {"単語", "意味"}
    if not required_cols.issubset(set(df.columns)):
        st.error("CSVに『単語』『意味』のヘッダーが必要です。例：単語,意味")
        st.stop()

    # =========================
    # セッション初期化
    # =========================
    ss = st.session_state
    if "remaining" not in ss:
        ss.remaining = df.to_dict("records")       # 未クリア問題のプール
    if "current" not in ss:
        ss.current = None                           # 現在の問題（dict）
    if "phase" not in ss:
        ss.phase = "quiz"                           # "quiz" or "feedback"
    if "start_time" not in ss:
        ss.start_time = None                        # 出題開始時刻
    if "hint" not in ss:
        ss.hint = ""                                # ヒント文字（1文字）
    if "last_outcome" not in ss:
        ss.last_outcome = None                      # ("correct"|"wrong"|"skip"|"timeout", word)
    if "answer_input" not in ss:
        ss.answer_input = ""                        # 入力欄の値

    # =========================
    # ユーティリティ
    # =========================
    def next_question():
        """次の問題へ（状態を“quiz”に戻す）"""
        if not ss.remaining:
            ss.current = None
            ss.phase = "done"
            return
        ss.current = random.choice(ss.remaining)
        ss.phase = "quiz"
        ss.start_time = time.time()
        ss.hint = ""
        ss.answer_input = ""
        ss.last_outcome = None

    def check_answer(ans: str) -> bool:
        """最初の2文字一致で正解判定（大文字小文字無視）"""
        word = ss.current["単語"]
        return word.lower().startswith(ans.strip().lower())

    # =========================
    # 終了ボタン
    # =========================
    if st.button("終了する"):
        st.write("テストを終了しました。")
        st.stop()

    # =========================
    # 出題 or 完了判定
    # =========================
    if ss.phase == "done":
        st.success("全問正解！お疲れさまでした🎉")
        st.stop()

    if ss.current is None and ss.phase == "quiz":
        next_question()

    # ここから画面本体
    if ss.phase == "quiz" and ss.current is not None:
        current = ss.current
        st.subheader(f"意味: {current['意味']}")

        # 入力欄（半角英数字のみ・2文字以上）
        ans = st.text_input(
            "単語の最初の2文字を入力してください（半角英数字）",
            key="answer_input",
            placeholder="ex) mo"
        )

        # 入力バリデーション
        if ans:
            if not ans.isascii():
                st.warning("⚠ 半角英数字で入力してください")
            elif len(ans.strip()) < 2:
                st.info("2文字以上入力してください")
            else:
                # 判定（この場では画面遷移せず、まず“feedback”へ移行）
                if check_answer(ans):
                    # 正解 → プールから除外
                    ss.remaining = [q for q in ss.remaining if q != current]
                    ss.last_outcome = ("correct", current["単語"])
                else:
                    # 不正解 → 正解表示して（プールには残す）
                    ss.last_outcome = ("wrong", current["単語"])
                ss.phase = "feedback"

        # スキップ
        if st.button("スキップ"):
            ss.last_outcome = ("skip", current["単語"])
            ss.phase = "feedback"

        # 経過時間でヒント／時間切れ
        if ss.start_time is not None:
            elapsed = time.time() - ss.start_time

            # 5秒で自動ヒント（1文字目）
            if elapsed >= 5 and not ss.hint:
                ss.hint = current["単語"][0]

            if ss.hint:
                st.info(f"ヒント: {ss.hint}")

            # 10秒で時間切れ → 正解を表示して feedback へ
            if elapsed >= 10:
                ss.last_outcome = ("timeout", current["単語"])
                ss.phase = "feedback"

    # ここから結果表示フェーズ（次に進むのはボタンのみ）
    if ss.phase == "feedback" and ss.last_outcome:
        status, word = ss.last_outcome
        if status == "correct":
            st.success(f"正解！ {word} 🎉")
        elif status == "wrong":
            st.error(f"不正解！正解は {word} です。")
        elif status == "skip":
            st.info(f"スキップしました。正解は {word} です。")
        elif status == "timeout":
            st.error(f"時間切れ！正解は {word} です。")

        # 入力欄は出さない（誤動作防止）
        if st.button("次の問題へ"):
            ss.current = None
            ss.phase = "quiz"
            ss.answer_input = ""
            ss.hint = ""
            ss.last_outcome = None
            # ここで next_question は呼ばず、次の再描画で呼ばれる

else:
    st.info("まずは単語リスト（CSVファイル, UTF-8形式）をアップロードしてください。")

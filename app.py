try:
    sheet = get_worksheet()
    sheet.append_row(["TEST", "0000000", "テスト単語", "接続OK"])
    st.success("✅ 書き込み成功！")
except Exception as e:
    import traceback
    st.error("❌ 書き込み失敗")
    st.text(traceback.format_exc())

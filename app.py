
import streamlit as st
import pandas as pd
from io import BytesIO
from alliance_balance_checker.detector import detect_sheet_type
from alliance_balance_checker.checker import check_texas, check_cowboy, check_mtt

st.set_page_config(page_title="牌局导表平账检测工具", layout="centered")

st.title("牌局导表平账检测工具")
uploaded_file = st.file_uploader("上传导出的 Excel 表格", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    sheet_type = detect_sheet_type(df)

    st.markdown(f"检测到导表类型：**{sheet_type}**")

    if sheet_type == "德州类":
        result_df, exportable = check_texas(df)
    elif sheet_type == "牛仔类":
        result_df, exportable = check_cowboy(df)
    elif sheet_type == "MTT类":
        result_df, exportable = check_mtt(df)
    else:
        st.error("无法识别导表类型或表格缺少关键字段")
        st.stop()

    if result_df.empty:
        st.success("所有牌局均已平账 ✅")
    else:
        st.warning(f"发现 {len(result_df)} 条不平账记录 ❌")
        st.dataframe(result_df)

        # 提供下载功能
        towrite = BytesIO()
        exportable.to_excel(towrite, index=False)
        towrite.seek(0)
        st.download_button("📥 下载不平账明细", towrite, file_name="unbalanced.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

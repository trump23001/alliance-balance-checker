
import streamlit as st
import pandas as pd

st.set_page_config(page_title="联盟收益智能分析工具", layout="wide")
st.title("📊 联盟收益分析大脑（初始版本）")

uploaded_files = st.file_uploader("上传多个导出 Excel 表格（支持多文件）", accept_multiple_files=True, type=["xlsx"])

if uploaded_files:
    st.success(f"共上传了 {len(uploaded_files)} 个文件，准备分析中...")

    for file in uploaded_files:
        st.subheader(f"📁 文件: {file.name}")
        try:
            df = pd.read_excel(file)
            st.write("预览前几行数据：")
            st.dataframe(df.head())
            # 👉 后续这里加入识别表格类型 + 判断平账逻辑
        except Exception as e:
            st.error(f"❌ 无法读取文件 {file.name}，错误信息: {str(e)}")
else:
    st.info("请上传包含联盟桌、朋友桌或俱乐部桌导出的 Excel 文件。")


import streamlit as st
import pandas as pd
import base64
import io

st.set_page_config(page_title="Alliance Balance Checker", layout="wide")

st.title("📊 联盟平账校验工具")
st.markdown("请上传多个导出的 Excel 表格（支持多文件），并点击下方按钮开始分析。")

uploaded_files = st.file_uploader("上传多个导出 Excel 表格（支持多文件）", type=["xlsx"], accept_multiple_files=True)
analyze_button = st.button("开始分析")

if uploaded_files and analyze_button:
    st.success(f"共上传了 {len(uploaded_files)} 个文件，准备分析中...")
    all_results = []
    summary = []

    def is_alliance_table(df):
        for col in df.columns:
            if '牌局类型' in col or '牌局類型' in col:
                type_values = df[col].astype(str).values
                for val in type_values[:5]:
                    if any(x in val for x in ['联盟', '聯盟']):
                        return True
        return False

    for file in uploaded_files:
        try:
            df = pd.read_excel(file)
        except Exception as e:
            st.error(f"{file.name} 加载失败: {e}")
            continue

        st.markdown(f"### 📂 文件: {file.name}")
        st.dataframe(df.head())

        if not is_alliance_table(df):
            st.info("该文件不是联盟桌导出表，已跳过。")
            continue

        if "总服务费" not in df.columns:
            st.warning("该表缺少 '总服务费' 字段，已跳过。")
            continue

        # 示例平账校验逻辑（可替换为实际的德州/牛仔/MTT判断）
        df = df[~df.iloc[:, 0].astype(str).str.contains("合计")]
        df["计算差值"] = df["总服务费"] - df.get("联盟服务费", 0) - df.get("俱乐部服务费", 0) - df.get("代理服务费", 0)
        df_unbalanced = df[df["计算差值"].abs() > 0.001]

        if not df_unbalanced.empty:
            st.error(f"❌ 文件 {file.name} 中存在不平账记录，共 {len(df_unbalanced)} 行")
            st.dataframe(df_unbalanced)
            df_unbalanced["来源文件"] = file.name
            all_results.append(df_unbalanced)
            summary.append(f"📄 {file.name}：{len(df_unbalanced)} 行不平账")
        else:
            st.success(f"✅ 文件 {file.name} 平账无误")

    if all_results:
        combined = pd.concat(all_results)
        csv = combined.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 下载所有不平账记录 CSV", data=csv, file_name="unbalanced_records.csv", mime="text/csv")
        st.markdown("### 📌 分析摘要")
        for item in summary:
            st.markdown(f"- {item}")
    else:
        st.success("🎉 所有上传的联盟桌文件均已平账！")


import streamlit as st
import pandas as pd

st.title("联盟牌局平账校验工具")

uploaded_file = st.file_uploader("上传 Excel 文件", type=["xlsx"])
if uploaded_file:
    df = pd.read_excel(uploaded_file)

    if '牌局ID' in df.columns and '最终战绩' in df.columns:
        grouped = df.groupby('牌局ID')
        result = []
        for game_id, group in grouped:
            total_final = group['最终战绩'].sum()
            if '总服务费' in group.columns and '保险' in group.columns and 'Jackpot贡献' in group.columns:
                total_fee = group['总服务费'].sum() + group['保险'].sum() + group['Jackpot贡献'].sum()
                balance_check = abs(total_final + total_fee) < 0.01
                result.append((game_id, total_final, total_fee, "✅ 平账" if balance_check else "❌ 不平账"))
        result_df = pd.DataFrame(result, columns=["牌局ID", "最终战绩总和", "平台收入总和", "是否平账"])
        st.dataframe(result_df)
    else:
        st.warning("未检测到所需字段（牌局ID、最终战绩、总服务费、保险、Jackpot贡献），请检查表格。")

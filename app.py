
import streamlit as st
import pandas as pd
import numpy as np
import os

st.set_page_config(page_title="不平账检测工具", layout="wide")
st.title("📊 不平账结果预览")

uploaded_files = st.file_uploader("上传多个 Excel 文件以进行平账分析", type=["xlsx"], accept_multiple_files=True)
start_analysis = st.button("开始分析")

simplified_fields = {
    "最终战绩": "final_result",
    "总服务费": "total_service_fee",
    "保险": "insurance",
    "jackpot贡献": "jackpot_contribution",
    "联盟jackpot分成": "union_jackpot_share",
    "俱乐部jackpot分成": "club_jackpot_share",
    "代理jackpot分成": "agent_jackpot_share",
    "jackpot贡献服务费": "jackpot_fee",
    "保险服务费": "insurance_fee",
    "货币类型": "currency_type",
    "牌局ID": "hand_id",
    "MTT名称": "mtt_name",
    "MTTID": "mtt_id",
    "联盟服务费": "union_service_fee",
    "俱乐部服务费": "club_service_fee",
    "代理服务费": "agent_service_fee",
    "总服务费": "total_service_fee",
    "带入": "buy_in",
    "带出": "buy_out",
    "联盟收益": "union_income",
    "俱乐部收益": "club_income",
    "代理收益": "agent_income",
}

traditional_fields = {
    "最終戰績": "final_result",
    "總服務費": "total_service_fee",
    "保險": "insurance",
    "jackpot貢獻": "jackpot_contribution",
    "聯盟jackpot分成": "union_jackpot_share",
    "俱樂部jackpot分成": "club_jackpot_share",
    "代理jackpot分成": "agent_jackpot_share",
    "jackpot貢獻服務費": "jackpot_fee",
    "保險服務費": "insurance_fee",
    "貨幣類型": "currency_type",
    "牌局ID": "hand_id",
    "MTT名稱": "mtt_name",
    "MTTID": "mtt_id",
    "聯盟服務費": "union_service_fee",
    "俱樂部服務費": "club_service_fee",
    "代理服務費": "agent_service_fee",
    "總服務費": "total_service_fee",
    "帶入": "buy_in",
    "帶出": "buy_out",
    "聯盟收益": "union_income",
    "俱樂部收益": "club_income",
    "代理收益": "agent_income",
}

def normalize_columns(df):
    columns = {}
    for col in df.columns:
        col_clean = str(col).strip()
        if col_clean in simplified_fields:
            columns[col] = simplified_fields[col_clean]
        elif col_clean in traditional_fields:
            columns[col] = traditional_fields[col_clean]
    df = df.rename(columns=columns)
    return df

def is_union_table(df):
    for idx, row in df.iterrows():
        if idx == 0:
            continue
        currency = row.get("currency_type")
        if pd.notna(currency) and str(currency).strip().upper() == "UC":
            return True
    return False

def analyze_union(df, file_name):
    df = normalize_columns(df)
    required_fields = [
        "final_result", "total_service_fee", "insurance", "jackpot_contribution",
        "union_jackpot_share", "club_jackpot_share", "agent_jackpot_share",
        "jackpot_fee", "insurance_fee", "hand_id"
    ]
    if not all(col in df.columns for col in required_fields):
        return []

    issues = []
    grouped = df.groupby("hand_id")
    for hand_id, group in grouped:
        result = group["final_result"].sum()
        fee = group["total_service_fee"].sum()
        ins = group["insurance"].sum()
        j_con = group["jackpot_contribution"].sum()
        u_share = group["union_jackpot_share"].sum()
        c_share = group["club_jackpot_share"].sum()
        a_share = group["agent_jackpot_share"].sum()
        j_fee = group["jackpot_fee"].sum()
        i_fee = group["insurance_fee"].sum()

        balance = result + fee + ins + j_con + u_share + c_share + a_share + j_fee - i_fee
        if abs(balance) > 0.01:
            issues.append(f"{file_name} 中牌局ID为 {hand_id} 出现不平账，差额为 {balance:.2f}")

    return issues

if start_analysis and uploaded_files:
    final_issues = []
    for file in uploaded_files:
        try:
            df = pd.read_excel(file)
            if is_union_table(df):
                issues = analyze_union(df, file.name)
                final_issues.extend(issues)
        except Exception as e:
            st.warning(f"{file.name} 读取失败：{e}")

    st.subheader("🔍 不平账结果：")
    if final_issues:
        for issue in final_issues:
            st.write("• " + issue)
    else:
        st.success("所有上传文件中的联盟桌都已平账 ✅")

import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="不平账结果预览", layout="centered")

st.title("📊 不平账结果预览")
st.caption("上传多个 Excel 文件以进行平账分析")

uploaded_files = st.file_uploader("Drag and drop files here", type="xlsx", accept_multiple_files=True)

def detect_table_type(df):
    columns = df.columns.astype(str).tolist()
    if any(k in columns for k in ["MTT名称", "MTT名稱"]):
        return "MTT"
    elif any(k in columns for k in ["带出", "帶出", "最终战绩", "最終戰績"]) and any(k in columns for k in ["联盟收益", "聯盟收益"]):
        return "Cowboy"
    elif any(k in columns for k in ["最终战绩", "最終戰績"]) and any(k in columns for k in ["总服务费", "總服務費"]):
        return "Texas"
    return "Unknown"

def normalize_columns(df):
    col_map = {
        "最终战绩": "result", "最終戰績": "result",
        "总服务费": "total_fee", "總服務費": "total_fee",
        "保险": "insurance", "保險": "insurance",
        "jackpot贡献": "jp_contrib", "jackpot貢獻": "jp_contrib",
        "联盟jackpot分成": "u_jp_share", "聯盟jackpot分成": "u_jp_share",
        "俱乐部jackpot分成": "c_jp_share", "俱樂部jackpot分成": "c_jp_share",
        "代理jackpot分成": "a_jp_share", "代理jackpot分成": "a_jp_share",
        "jackpot贡献服务费": "jp_fee", "jackpot貢獻服務費": "jp_fee",
        "保险服务费": "insurance_fee", "保險服務費": "insurance_fee",

        "带出": "out", "帶出": "out",
        "带入": "in", "帶入": "in",
        "联盟收益": "u_profit", "聯盟收益": "u_profit",
        "俱乐部收益": "c_profit", "俱樂部收益": "c_profit",
        "代理收益": "a_profit", "代理收益": "a_profit",

        "MTT名称": "mtt_name", "MTT名稱": "mtt_name",
        "MTTID": "mtt_id",
        "联盟服务费": "u_fee", "聯盟服務費": "u_fee",
        "俱乐部服务费": "c_fee", "俱樂部服務費": "c_fee",
        "代理服务费": "a_fee", "代理服務費": "a_fee",
    }
    df = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})
    return df

def check_texas(df):
    df = normalize_columns(df)
    if "result" not in df.columns or "total_fee" not in df.columns:
        return True
    df["sum"] = df[["result", "total_fee", "insurance", "jp_contrib",
                    "u_jp_share", "c_jp_share", "a_jp_share", "jp_fee"]].fillna(0).sum(axis=1)                 - df["insurance_fee"].fillna(0)
    return df[abs(df["sum"]) > 0.01].empty

def check_cowboy(df):
    df = normalize_columns(df)
    if "out" not in df.columns or "in" not in df.columns or "result" not in df.columns:
        return True
    df["carry_check"] = df["out"].fillna(0) - df["in"].fillna(0) - df["result"].fillna(0)
    df["profit_check"] = df[["result", "u_profit", "c_profit", "a_profit"]].fillna(0).sum(axis=1)
    return df[abs(df["carry_check"]) > 0.01].empty and df[abs(df["profit_check"]) > 0.01].empty

def check_mtt(df):
    df = normalize_columns(df)
    if "total_fee" not in df.columns or "u_fee" not in df.columns:
        return True
    df["diff"] = df["total_fee"].fillna(0) - df[["u_fee", "c_fee", "a_fee"]].fillna(0).sum(axis=1)
    return df[abs(df["diff"]) > 0.01].empty

if st.button("开始分析") and uploaded_files:
    all_pass = True
    for file in uploaded_files:
        df = pd.read_excel(file)
        table_type = detect_table_type(df)
        if table_type == "Texas":
            result = check_texas(df)
        elif table_type == "Cowboy":
            result = check_cowboy(df)
        elif table_type == "MTT":
            result = check_mtt(df)
        else:
            result = True
        if not result:
            all_pass = False

    st.subheader("🔍 不平账结果：")
    if all_pass:
        st.success("所有上传文件中的联盟桌都已平账 ✅")
    else:
        st.error("发现不平账的牌桌，请检查详情 ❌")
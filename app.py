import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="导表平账检测工具", layout="wide")

# 识别字段名的繁简体映射
texas_fields = {
    "最终战绩": ["最终战绩", "最終戰績"],
    "总服务费": ["总服务费", "總服務費"],
    "保险": ["保险", "保險"],
    "jackpot贡献": ["jackpot贡献", "jackpot貢獻"],
    "联盟jackpot分成": ["联盟jackpot分成", "聯盟jackpot分成"],
    "俱乐部jackpot分成": ["俱乐部jackpot分成", "俱樂部jackpot分成"],
    "代理jackpot分成": ["代理jackpot分成"],
    "jackpot贡献服务费": ["jackpot贡献服务费", "jackpot貢獻服務費"],
    "保险服务费": ["保险服务费", "保險服務費"],
    "牌局ID": ["牌局ID"]
}

cowboy_fields = {
    "带出": ["带出", "帶出"],
    "带入": ["带入", "帶入"],
    "最终战绩": ["最终战绩", "最終戰績"],
    "联盟收益": ["联盟收益", "聯盟收益"],
    "俱乐部收益": ["俱乐部收益", "俱樂部收益"],
    "代理收益": ["代理收益", "代理收益"],
    "牌局ID": ["牌局ID"]
}

mtt_fields = {
    "总服务费": ["总服务费", "總服務費"],
    "联盟服务费": ["联盟服务费", "聯盟服務費"],
    "俱乐部服务费": ["俱乐部服务费", "俱樂部服務費"],
    "代理服务费": ["代理服务费", "代理服務費"],
    "MTT ID": ["MTT ID"]
}

def match_fields(columns, field_map):
    matched = {}
    for key, variants in field_map.items():
        for v in variants:
            if v in columns:
                matched[key] = v
                break
    return matched

def detect_file_type(df):
    columns = df.columns.tolist()
    if any("MTT" in str(col).upper() or "比赛" in str(col) for col in columns):
        return "MTT"
    elif any("下注量" in str(col) for col in columns):
        return "COWBOY"
    elif any("jackpot" in str(col).lower() for col in columns):
        return "TEXAS"
    else:
        return "UNKNOWN"

def check_texas(df):
    df = df.dropna(subset=["牌局ID"], errors="ignore")
    df_grouped = df.groupby("牌局ID").agg({
        "最终战绩": "sum",
        "总服务费": "sum",
        "保险": "sum",
        "jackpot贡献": "sum",
        "联盟jackpot分成": "sum",
        "俱乐部jackpot分成": "sum",
        "代理jackpot分成": "sum",
        "jackpot贡献服务费": "sum",
        "保险服务费": "sum"
    }).reset_index()

    df_grouped["差值"] = df_grouped["最终战绩"] + df_grouped["总服务费"] + df_grouped["保险"] + df_grouped["jackpot贡献"] + df_grouped["联盟jackpot分成"] + df_grouped["俱乐部jackpot分成"] + df_grouped["代理jackpot分成"] + df_grouped["jackpot贡献服务费"] - df_grouped["保险服务费"]
    df_unbalanced = df_grouped[np.abs(df_grouped["差值"]) >= 0.001]
    return df_unbalanced

def check_cowboy(df):
    df["战绩差值"] = df["带出"] - df["带入"] - df["最终战绩"]
    df["分润差值"] = df["最终战绩"] + df["联盟收益"] + df["俱乐部收益"] + df["代理收益"]
    df_war_unbalanced = df[np.abs(df["战绩差值"]) >= 0.001]
    df_profit_unbalanced = df[np.abs(df["分润差值"]) >= 0.001]
    return df_war_unbalanced, df_profit_unbalanced

def check_mtt(df):
    df["差值"] = df["总服务费"] - (df["联盟服务费"] + df["俱乐部服务费"] + df["代理服务费"])
    df_unbalanced = df[np.abs(df["差值"]) >= 0.001]
    return df_unbalanced

st.title("🧾 联盟导表平账检测工具")

uploaded_file = st.file_uploader("上传导出 Excel 表格", type=["xlsx"])
if uploaded_file:
    df_raw = pd.read_excel(uploaded_file, dtype=str)
    df_raw = df_raw.fillna(0)
    df_raw.replace(" ", 0, inplace=True)
    df_raw.replace("", 0, inplace=True)
    df_raw = df_raw.apply(pd.to_numeric, errors='ignore')

    file_type = detect_file_type(df_raw)
    st.info(f"识别到导表类型：{file_type}")

    if file_type == "TEXAS":
        fields = match_fields(df_raw.columns, texas_fields)
        df = df_raw.rename(columns={v: k for k, v in fields.items()})
        result = check_texas(df)
        if result.empty:
            st.success("✅ 全部牌局平账")
        else:
            st.error("❌ 存在不平账的牌局")
            st.dataframe(result)
            st.download_button("📥 下载不平账牌局", result.to_excel(index=False), file_name="texas_unbalanced.xlsx")

    elif file_type == "COWBOY":
        fields = match_fields(df_raw.columns, cowboy_fields)
        df = df_raw.rename(columns={v: k for k, v in fields.items()})
        war_unbal, profit_unbal = check_cowboy(df)
        if war_unbal.empty and profit_unbal.empty:
            st.success("✅ 全部平账")
        else:
            if not war_unbal.empty:
                st.error("⚠️ 战绩不平账：")
                st.dataframe(war_unbal)
                st.download_button("📥 下载战绩不平账", war_unbal.to_excel(index=False), file_name="cowboy_war_unbalanced.xlsx")
            if not profit_unbal.empty:
                st.error("⚠️ 分润不平账：")
                st.dataframe(profit_unbal)
                st.download_button("📥 下载分润不平账", profit_unbal.to_excel(index=False), file_name="cowboy_profit_unbalanced.xlsx")

    elif file_type == "MTT":
        fields = match_fields(df_raw.columns, mtt_fields)
        df = df_raw.rename(columns={v: k for k, v in fields.items()})
        result = check_mtt(df)
        if result.empty:
            st.success("✅ 所有玩家服务费平账")
        else:
            st.error("❌ 存在服务费不平账的玩家")
            st.dataframe(result)
            st.download_button("📥 下载不平账玩家", result.to_excel(index=False), file_name="mtt_unbalanced.xlsx")

    else:
        st.warning("无法识别导表类型，请检查文件内容。")


import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="联盟导表平账校验工具", layout="wide")

st.title("🧾 联盟导表平账校验工具")

uploaded_file = st.file_uploader("请上传德州/牛仔/MTT导出的表格文件（支持xls/xlsx）", type=["xls", "xlsx"])

def normalize_col(col):
    mapping = {
        "最终战绩": ["最终战绩", "最終戰績"],
        "总服务费": ["总服务费", "總服務費"],
        "保险": ["保险", "保險"],
        "Jackpot贡献": ["jackpot贡献", "jackpot貢獻"],
        "联盟Jackpot分成": ["联盟jackpot分成", "聯盟jackpot分成"],
        "俱乐部Jackpot分成": ["俱乐部jackpot分成", "俱樂部jackpot分成"],
        "代理Jackpot分成": ["代理jackpot分成"],
        "Jackpot贡献服务费": ["jackpot贡献服务费", "jackpot貢獻服務費"],
        "保险服务费": ["保险服务费", "保險服務費"],
        "带出": ["带出", "帶出"],
        "带入": ["带入", "帶入"],
        "联盟收益": ["联盟收益", "聯盟收益"],
        "俱乐部收益": ["俱乐部收益", "俱樂部收益"],
        "代理收益": ["代理收益"],
        "MTTID": ["MTTID"],
        "玩家昵称": ["玩家昵称"],
        "代理昵称": ["代理昵称"],
        "俱乐部名称": ["俱乐部名称"],
        "联盟名称": ["联盟名称"],
        "联盟服务费": ["联盟服务费", "聯盟服務費"],
        "俱乐部服务费": ["俱乐部服务费", "俱樂部服務費"],
        "代理服务费": ["代理服务费", "代理服務費"]
    }
    for std, aliases in mapping.items():
        if col in aliases:
            return std
    return col

def identify_sheet_type(df):
    header = ''.join(df.columns.astype(str))
    if 'mtt' in header.lower() or '比赛' in header:
        return 'MTT'
    elif '下注量' in header or '带出' in header or '帶出' in header:
        return '牛仔'
    elif any("jackpot" in col.lower() for col in df.columns):
        return '德州'
    else:
        return '未知'

def check_texas(df):
    df = df.rename(columns=lambda x: normalize_col(x))
    df = df[~df['牌局ID'].astype(str).str.contains("总计", na=False)]
    df_grouped = df.groupby("牌局ID").agg({
        "最终战绩": "sum",
        "总服务费": "sum",
        "保险": "sum",
        "Jackpot贡献": "sum",
        "联盟Jackpot分成": "sum",
        "俱乐部Jackpot分成": "sum",
        "代理Jackpot分成": "sum",
        "Jackpot贡献服务费": "sum",
        "保险服务费": "sum",
    }).reset_index()
    df_grouped["差值"] = (
        df_grouped["最终战绩"]
        + df_grouped["总服务费"]
        + df_grouped["保险"]
        + df_grouped["Jackpot贡献"]
        + df_grouped["联盟Jackpot分成"]
        + df_grouped["俱乐部Jackpot分成"]
        + df_grouped["代理Jackpot分成"]
        + df_grouped["Jackpot贡献服务费"]
        - df_grouped["保险服务费"]
    )
    result = df_grouped[np.abs(df_grouped["差值"]) > 0.001]
    return result

def check_cowboy(df):
    df = df.rename(columns=lambda x: normalize_col(x))
    df["战绩差值"] = df["带出"] - df["带入"] - df["最终战绩"]
    df["分润差值"] = df["最终战绩"] + df["联盟收益"] + df["俱乐部收益"] + df["代理收益"]
    wrong_1 = df[np.abs(df["战绩差值"]) > 0.001]
    wrong_2 = df[np.abs(df["分润差值"]) > 0.001]
    return wrong_1, wrong_2

def check_mtt(df):
    df = df.rename(columns=lambda x: normalize_col(x))
    df["差值"] = df["总服务费"] - (
        df["联盟服务费"] + df["俱乐部服务费"] + df["代理服务费"]
    )
    wrong = df[np.abs(df["差值"]) > 0.001]
    return wrong

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    df.columns = [normalize_col(c) for c in df.columns]
    sheet_type = identify_sheet_type(df)
    st.info(f"识别到导表类型：{sheet_type}")

    if sheet_type == "德州":
        result = check_texas(df)
        if result.empty:
            st.success("✅ 全部平账！")
        else:
            st.error("❌ 存在不平账的牌局")
            st.dataframe(result)
            st.download_button("下载不平账明细", result.to_csv(index=False).encode("utf-8"), "texas_unbalanced.csv")

    elif sheet_type == "牛仔":
        wrong1, wrong2 = check_cowboy(df)
        if wrong1.empty and wrong2.empty:
            st.success("✅ 全部平账！")
        else:
            if not wrong1.empty:
                st.error("❌ 存在战绩不平账")
                st.dataframe(wrong1)
                st.download_button("下载战绩不平账明细", wrong1.to_csv(index=False).encode("utf-8"), "cowboy_stat.csv")
            if not wrong2.empty:
                st.error("❌ 存在分润不平账")
                st.dataframe(wrong2)
                st.download_button("下载分润不平账明细", wrong2.to_csv(index=False).encode("utf-8"), "cowboy_profit.csv")

    elif sheet_type == "MTT":
        wrong = check_mtt(df)
        if wrong.empty:
            st.success("✅ 全部平账！")
        else:
            st.error("❌ 存在不平账玩家")
            st.dataframe(wrong)
            st.download_button("下载不平账玩家", wrong.to_csv(index=False).encode("utf-8"), "mtt_unbalanced.csv")

    else:
        st.warning("⚠️ 无法识别导表类型")

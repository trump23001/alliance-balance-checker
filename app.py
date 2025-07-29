
import streamlit as st
import pandas as pd
import io

def detect_file_type(df):
    columns = df.columns.tolist()
    if "牌局ID" in columns or "Game ID" in columns:
        return "德州类"
    elif "MTTID" in columns:
        return "MTT"
    elif "战绩" in columns and "带入" in columns and "带出" in columns:
        return "牛仔"
    else:
        return "未知"

def check_texas(df):
    df = df.copy()
    df["最终战绩"] = pd.to_numeric(df["最终战绩"], errors='coerce')
    df["总服务费"] = pd.to_numeric(df["总服务费"], errors='coerce')
    df["保险"] = pd.to_numeric(df["保险"], errors='coerce')
    df["Jackpot贡献"] = pd.to_numeric(df["Jackpot贡献"], errors='coerce')
    df["联盟Jackpot分成"] = pd.to_numeric(df["联盟Jackpot分成"], errors='coerce')
    df["俱乐部Jackpot分成"] = pd.to_numeric(df["俱乐部Jackpot分成"], errors='coerce')
    df["代理Jackpot分成"] = pd.to_numeric(df["代理Jackpot分成"], errors='coerce')
    df["Jackpot贡献服务费"] = pd.to_numeric(df.get("Jackpot贡献服务费", 0), errors='coerce')
    df["保险服务费"] = pd.to_numeric(df.get("保险服务费", 0), errors='coerce')

    grouped = df.groupby("牌局ID").agg({
        "最终战绩": "sum",
        "总服务费": "sum",
        "保险": "sum",
        "Jackpot贡献": "sum",
        "联盟Jackpot分成": "sum",
        "俱乐部Jackpot分成": "sum",
        "代理Jackpot分成": "sum",
        "Jackpot贡献服务费": "sum",
        "保险服务费": "sum"
    }).reset_index()

    grouped["差值"] = grouped["最终战绩"] + grouped["总服务费"] + grouped["保险"] + grouped["Jackpot贡献"] + grouped["联盟Jackpot分成"] + grouped["俱乐部Jackpot分成"] + grouped["代理Jackpot分成"] + grouped["Jackpot贡献服务费"] - grouped["保险服务费"]
    result = grouped[abs(grouped["差值"]) > 0.01]
    return result

def check_niuzai(df):
    df = df.copy()
    df["带入"] = pd.to_numeric(df["带入"], errors='coerce')
    df["带出"] = pd.to_numeric(df["带出"], errors='coerce')
    df["战绩"] = pd.to_numeric(df["战绩"], errors='coerce')
    df["联盟收益"] = pd.to_numeric(df["联盟收益"], errors='coerce')
    df["俱乐部收益"] = pd.to_numeric(df["俱乐部收益"], errors='coerce')
    df["代理收益"] = pd.to_numeric(df["代理收益"], errors='coerce')

    df["战绩差值"] = df["带出"] - df["带入"] - df["战绩"]
    df["分润差值"] = df["战绩"] + df["联盟收益"] + df["俱乐部收益"] + df["代理收益"]

    war_record_issue = df[abs(df["战绩差值"]) > 0.01]
    share_issue = df[abs(df["分润差值"]) > 0.01]

    return war_record_issue, share_issue

def check_mtt(df):
    df = df.copy()
    df["总服务费"] = pd.to_numeric(df["总服务费"], errors='coerce')
    df["联盟服务费"] = pd.to_numeric(df["联盟服务费"], errors='coerce')
    df["俱乐部服务费"] = pd.to_numeric(df["俱乐部服务费"], errors='coerce')
    df["代理服务费"] = pd.to_numeric(df["代理服务费"], errors='coerce')

    df["差值"] = df["总服务费"] - (df["联盟服务费"] + df["俱乐部服务费"] + df["代理服务费"])
    result = df[abs(df["差值"]) > 0.01][["MTTID", "玩家昵称", "代理昵称", "俱乐部名称", "联盟名称", "差值"]]
    return result

st.title("牌局导表平账检测工具")

uploaded_file = st.file_uploader("上传导出的 Excel 表格", type=["xlsx"])
if uploaded_file:
    df = pd.read_excel(uploaded_file)
    file_type = detect_file_type(df)
    st.write(f"检测到导表类型：**{file_type}**")

    if file_type == "德州类":
        result = check_texas(df)
        st.write("不平账牌局如下：")
        st.dataframe(result)
        st.download_button("下载不平账牌局 Excel", result.to_excel(index=False), "unbalanced_texas.xlsx")
    elif file_type == "牛仔":
        war_issue, share_issue = check_niuzai(df)
        if not war_issue.empty:
            st.write("战绩不平账：")
            st.dataframe(war_issue[["牌局ID", "玩家昵称", "俱乐部名称", "联盟名称", "带入", "带出", "战绩", "战绩差值"]])
        if not share_issue.empty:
            st.write("分润不平账：")
            st.dataframe(share_issue[["牌局ID", "玩家昵称", "俱乐部名称", "联盟名称", "战绩", "联盟收益", "俱乐部收益", "代理收益", "分润差值"]])
    elif file_type == "MTT":
        result = check_mtt(df)
        st.write("MTT 服务费分润不平账记录：")
        st.dataframe(result)
        st.download_button("下载不平账记录 Excel", result.to_excel(index=False), "unbalanced_mtt.xlsx")
    else:
        st.error("无法识别导表类型，请确认格式。")

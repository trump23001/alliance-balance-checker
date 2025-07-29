import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="联盟牌局平账校验工具", layout="wide")
st.title("联盟牌局平账校验工具")

uploaded_file = st.file_uploader("上传 Excel 文件", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)

    required_columns = [
        "牌局ID", "最终战绩", "总服务费", "保险", "Jackpot贡献",
        "联盟Jackpot分成", "俱乐部Jackpot分成", "代理Jackpot分成"
    ]

    if not all(col in df.columns for col in required_columns):
        st.error("Excel 文件缺少必要的列。")
    else:
        df["最终战绩"] = pd.to_numeric(df["最终战绩"], errors="coerce").fillna(0)
        df["总服务费"] = pd.to_numeric(df["总服务费"], errors="coerce").fillna(0)
        df["保险"] = pd.to_numeric(df["保险"], errors="coerce").fillna(0)
        df["Jackpot贡献"] = pd.to_numeric(df["Jackpot贡献"], errors="coerce").fillna(0)
        df["联盟Jackpot分成"] = pd.to_numeric(df["联盟Jackpot分成"], errors="coerce").fillna(0)
        df["俱乐部Jackpot分成"] = pd.to_numeric(df["俱乐部Jackpot分成"], errors="coerce").fillna(0)
        df["代理Jackpot分成"] = pd.to_numeric(df["代理Jackpot分成"], errors="coerce").fillna(0)

        df["计算结果"] = df["最终战绩"] + df["总服务费"] + df["保险"] + df["Jackpot贡献"] +                      df["联盟Jackpot分成"] + df["俱乐部Jackpot分成"] + df["代理Jackpot分成"]

        df["是否平账"] = df["计算结果"].apply(lambda x: "是" if abs(x) < 0.01 else "否")

        result_df = df[df["是否平账"] == "否"].copy()

        if not result_df.empty:
            st.dataframe(result_df[["牌局ID", "最终战绩", "总服务费", "保险", "Jackpot贡献",
                                    "联盟Jackpot分成", "俱乐部Jackpot分成", "代理Jackpot分成", "计算结果", "是否平账"]])

            towrite = io.BytesIO()
            result_df.to_excel(towrite, index=False, engine='openpyxl')
            towrite.seek(0)
            st.download_button("下载不平账结果", data=towrite, file_name="不平账牌局.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        else:
            st.success("所有牌局都已平账。")

import streamlit as st
import pandas as pd

st.title("联盟牌局平账校验工具")

uploaded_file = st.file_uploader("上传 Excel 文件", type=["xlsx"])

if uploaded_file is not None:
    try:
        df = pd.read_excel(uploaded_file)

        required_columns = [
            "牌局ID", "最终战绩", "总服务费", "保险", "Jackpot贡献",
            "联盟Jackpot分成", "俱乐部Jackpot分成", "代理Jackpot分成"
        ]
        if not all(col in df.columns for col in required_columns):
            st.error("Excel 文件缺少必要的列。")
        else:
            df["最终战绩"] = pd.to_numeric(df["最终战绩"], errors='coerce').fillna(0)
            df["总服务费"] = pd.to_numeric(df["总服务费"], errors='coerce').fillna(0)
            df["保险"] = pd.to_numeric(df["保险"], errors='coerce').fillna(0)
            df["Jackpot贡献"] = pd.to_numeric(df["Jackpot贡献"], errors='coerce').fillna(0)
            df["联盟Jackpot分成"] = pd.to_numeric(df["联盟Jackpot分成"], errors='coerce').fillna(0)
            df["俱乐部Jackpot分成"] = pd.to_numeric(df["俱乐部Jackpot分成"], errors='coerce').fillna(0)
            df["代理Jackpot分成"] = pd.to_numeric(df["代理Jackpot分成"], errors='coerce').fillna(0)

            df["平账校验"] = (
                df["最终战绩"] +
                df["总服务费"] +
                df["保险"] +
                df["Jackpot贡献"] +
                df["联盟Jackpot分成"] +
                df["俱乐部Jackpot分成"] +
                df["代理Jackpot分成"]
            ).round(2)

            df["是否平账"] = df["平账校验"].apply(lambda x: "✅" if abs(x) < 0.01 else "❌")

            result_df = df[df["是否平账"] == "❌"][["牌局ID", "最终战绩", "总服务费", "保险", "Jackpot贡献", "联盟Jackpot分成", "俱乐部Jackpot分成", "代理Jackpot分成", "平账校验", "是否平账"]]

            st.dataframe(result_df)

            # 提供下载
            csv = result_df.to_csv(index=False).encode("utf-8-sig")
            st.download_button(
                label="下载不平账记录",
                data=csv,
                file_name="不平账记录.csv",
                mime="text/csv"
            )
    except Exception as e:
        st.error(f"处理文件时出错: {e}")
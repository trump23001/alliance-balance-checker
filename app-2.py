import streamlit as st
import pandas as pd

st.set_page_config(page_title="联盟牌局平账校验工具", layout="wide")
st.title("联盟牌局平账校验工具")

uploaded_file = st.file_uploader("上传 Excel 文件", type=["xlsx"])
if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file)
        required_columns = ["牌局ID", "最终战绩", "总服务费", "保险", "Jackpot贡献", "联盟Jackpot分成", "俱乐部Jackpot分成", "代理Jackpot分成"]
        if not all(col in df.columns for col in required_columns):
            st.error("Excel 文件缺少必要的列。")
        else:
            df["校验值"] = (
                df["最终战绩"] + df["总服务费"] + df["保险"] +
                df["Jackpot贡献"] + df["联盟Jackpot分成"] +
                df["俱乐部Jackpot分成"] + df["代理Jackpot分成"]
            ).round(2)
            df["是否平账"] = df["校验值"] == 0

            # 仅筛选不平账数据
            df_unbalanced = df.loc[~df["是否平账"], [
                "牌局ID", "最终战绩", "总服务费", "保险",
                "Jackpot贡献", "联盟Jackpot分成", "俱乐部Jackpot分成",
                "代理Jackpot分成", "校验值", "是否平账"
            ]]

            if df_unbalanced.empty:
                st.success("所有牌局都已平账 ✅")
            else:
                st.warning(f"共发现 {len(df_unbalanced)} 条不平账记录 ❌")
                st.dataframe(df_unbalanced)

                st.download_button(
                    label="下载不平账记录",
                    data=df_unbalanced.to_excel(index=False, engine="openpyxl"),
                    file_name="不平账牌局.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
    except Exception as e:
        st.error(f"读取 Excel 文件失败：{e}")

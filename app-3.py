
import streamlit as st
import pandas as pd
import io

st.title("联盟牌局平账校验工具")

uploaded_file = st.file_uploader("上传 Excel 文件", type=["xlsx"])
if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file)

        # 检查必须字段是否都存在
        required_columns = ["最终战绩", "总服务费", "保险", "jackpot贡献", "联盟jackpot分成", "俱乐部jackpot分成", "代理jackpot分成"]
        if not all(col in df.columns for col in required_columns):
            st.error("Excel 文件缺少必要的列。")
        else:
            # 将非数字列处理为0（可能存在 - 或空值）
            for col in required_columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

            # 计算差值并筛选出不平账的牌局
            df["差值"] = df["最终战绩"] + df["总服务费"] + df["保险"] + df["jackpot贡献"] + df["联盟jackpot分成"] + df["俱乐部jackpot分成"] + df["代理jackpot分成"]
            df_filtered = df[df["差值"].round(2) != 0]

            if df_filtered.empty:
                st.success("所有牌局都已平账，无异常记录。")
            else:
                st.subheader("存在不平账的牌局：")
                st.dataframe(df_filtered)

                # 提供下载
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df_filtered.to_excel(writer, index=False)
                st.download_button(
                    label="下载不平账牌局",
                    data=output.getvalue(),
                    file_name="unbalanced_records.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
    except Exception as e:
        st.error(f"文件处理出错：{e}")

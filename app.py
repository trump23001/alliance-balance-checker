
import streamlit as st
import pandas as pd
import io

st.title("联盟牌局平账校验工具（修正版）")

uploaded_file = st.file_uploader("上传导出的 Excel 文件（.xlsx）", type="xlsx")

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file)

        required_fields = [
            "牌局ID", "最终战绩", "总服务费", "保险", "jackpot贡献",
            "联盟jackpot分成", "俱乐部jackpot分成", "代理jackpot分成",
            "jackpot贡献服务费", "保险服务费"
        ]

        missing = [col for col in required_fields if col not in df.columns]
        if missing:
            st.error(f"缺少以下必要字段：{', '.join(missing)}")
        else:
            grouped = df.groupby("牌局ID")[required_fields[1:]].sum()
            grouped["差值"] = (
                grouped["最终战绩"]
                + grouped["总服务费"]
                + grouped["保险"]
                + grouped["jackpot贡献"]
                + grouped["联盟jackpot分成"]
                + grouped["俱乐部jackpot分成"]
                + grouped["代理jackpot分成"]
                + grouped["jackpot贡献服务费"]
                - grouped["保险服务费"]
            )

            tolerance = 0.01
            unbalanced = grouped[grouped["差值"].abs() > tolerance]

            st.success(f"共发现 {len(unbalanced)} 个不平账的牌局")
            st.dataframe(unbalanced)

            # 下载链接
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                unbalanced.to_excel(writer, index=True, sheet_name='不平账牌局')
            st.download_button(
                label="下载不平账牌局 Excel",
                data=output.getvalue(),
                file_name="不平账牌局.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    except Exception as e:
        st.error(f"处理文件出错：{e}")

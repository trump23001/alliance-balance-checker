
import streamlit as st
import pandas as pd

st.set_page_config(page_title="是否平账检查工具", layout="wide")
st.title("🧾 联盟牌局是否平账检查工具")

uploaded_file = st.file_uploader("上传 Excel 文件（包含所有牌局）", type=["xlsx"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file)

        required_columns = [
            "牌局ID", "最终战绩", "总服务费", "保险",
            "jackpot贡献", "联盟jackpot分成",
            "俱乐部jackpot分成", "代理jackpot分成"
        ]

        if not all(col in df.columns for col in required_columns):
            st.error("❌ 缺少必要的列，请检查表头是否包括：\n" + ", ".join(required_columns))
        else:
            # 按牌局ID分组计算
            grouped = df.groupby("牌局ID").agg({
                "最终战绩": "sum",
                "总服务费": "sum",
                "保险": "sum",
                "jackpot贡献": "sum",
                "联盟jackpot分成": "sum",
                "俱乐部jackpot分成": "sum",
                "代理jackpot分成": "sum"
            }).reset_index()

            # 计算是否平账
            grouped["平账校验值"] = grouped["最终战绩"] + grouped["总服务费"] + grouped["保险"] + grouped["jackpot贡献"] + grouped["联盟jackpot分成"] + grouped["俱乐部jackpot分成"] + grouped["代理jackpot分成"]
            grouped["是否平账"] = grouped["平账校验值"].apply(lambda x: "✅ 是" if abs(x) < 0.01 else "❌ 否")

            st.success(f"共检测到 {len(grouped)} 个牌局")
            st.dataframe(grouped, use_container_width=True)

            # 提供下载
            csv = grouped.to_csv(index=False).encode("utf-8-sig")
            st.download_button("📥 下载平账检查结果", data=csv, file_name="平账结果.csv", mime="text/csv")

    except Exception as e:
        st.error(f"读取文件失败，请确认格式正确。\n错误信息: {e}")

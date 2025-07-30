import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Alliance Balance Checker", layout="wide")

st.title("🧮 多文件联盟桌平账校验工具")

uploaded_files = st.file_uploader("上传多个导出 Excel 表格（支持多文件）", type=["xlsx"], accept_multiple_files=True)

session_key = "uploaded_dfs"
if session_key not in st.session_state:
    st.session_state[session_key] = {}

if uploaded_files:
    st.success(f"共上传了 {len(uploaded_files)} 个文件，准备分析中…")

    for uploaded_file in uploaded_files:
        try:
            df = pd.read_excel(uploaded_file)
            st.session_state[session_key][uploaded_file.name] = df
            st.markdown(f"### 📂 文件: {uploaded_file.name}")
            st.dataframe(df.head(), use_container_width=True)
        except Exception as e:
            st.error(f"无法读取 {uploaded_file.name}，错误信息：{e}")

if st.button("开始分析") and st.session_state[session_key]:
    st.subheader("📊 不平账结果预览")

    def normalize_col(col):
        return str(col).strip().replace("：", "").replace(":", "")

    simplified_col_map = {
        "最终战绩": ["最终战绩", "最終戰績"],
        "总服务费": ["总服务费", "總服務費"],
        "保险": ["保险", "保險"],
        "jackpot贡献": ["jackpot贡献", "jackpot貢獻"],
        "联盟jackpot分成": ["联盟jackpot分成", "聯盟jackpot分成"],
        "俱乐部jackpot分成": ["俱乐部jackpot分成", "俱樂部jackpot分成"],
        "代理jackpot分成": ["代理jackpot分成", "代理jackpot分成"],
        "jackpot贡献服务费": ["jackpot贡献服务费", "jackpot貢獻服務費"],
        "保险服务费": ["保险服务费", "保險服務費"],
    }

    result_rows = []
    for filename, df in st.session_state[session_key].items():
        df.columns = [normalize_col(c) for c in df.columns]

        # 忽略合计行
        df_filtered = df[~df.iloc[:, 0].astype(str).str.contains("合计")]

        if "货币类型" in df_filtered.columns:
            money_col = "货币类型"
        elif "貨幣類型" in df_filtered.columns:
            money_col = "貨幣類型"
        else:
            continue

        if not any(df_filtered[money_col].astype(str).str.contains("UC|联盟币|聯盟幣", case=False, na=False)):
            continue  # 跳过非联盟桌

        # 德州类判断
        type_keywords = ["德州", "短牌", "奥马哈", "德州撲克", "奧馬哈"]
        if any(tk in " ".join(df.columns) for tk in type_keywords):
            # 建立映射列
            col_map = {}
            for key, aliases in simplified_col_map.items():
                for alias in aliases:
                    for col in df.columns:
                        if normalize_col(col) == normalize_col(alias):
                            col_map[key] = col
            if len(col_map) < 9:
                continue

            df_check = df_filtered.copy()
            df_check["是否平账"] = (
                df_check[col_map["最终战绩"]].fillna(0)
                + df_check[col_map["总服务费"]].fillna(0)
                + df_check[col_map["保险"]].fillna(0)
                + df_check[col_map["jackpot贡献"]].fillna(0)
                + df_check[col_map["联盟jackpot分成"]].fillna(0)
                + df_check[col_map["俱乐部jackpot分成"]].fillna(0)
                + df_check[col_map["代理jackpot分成"]].fillna(0)
                + df_check[col_map["jackpot贡献服务费"]].fillna(0)
                - df_check[col_map["保险服务费"]].fillna(0)
            ).round(2)

            df_wrong = df_check[df_check["是否平账"] != 0].copy()
            if not df_wrong.empty:
                df_wrong.insert(0, "来源文件", filename)
                result_rows.append(df_wrong)

    if result_rows:
        result_all = pd.concat(result_rows, ignore_index=True)
        st.dataframe(result_all, use_container_width=True)

        to_download = io.BytesIO()
        with pd.ExcelWriter(to_download, engine="xlsxwriter") as writer:
            result_all.to_excel(writer, index=False)
        to_download.seek(0)

        st.download_button(
            label="📥 下载不平账结果 Excel",
            data=to_download,
            file_name="unbalanced_results.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    else:
        st.success("所有上传文件中的联盟桌都已平账 ✅")

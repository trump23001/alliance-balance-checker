
import streamlit as st
import pandas as pd

def normalize_columns(df):
    column_map = {
        "最终战绩": ["最终战绩", "最終戰績"],
        "总服务费": ["总服务费", "總服務費"],
        "保险": ["保险", "保險"],
        "jackpot贡献": ["jackpot贡献", "jackpot貢獻"],
        "联盟jackpot分成": ["联盟jackpot分成", "聯盟jackpot分成"],
        "俱乐部jackpot分成": ["俱乐部jackpot分成", "俱樂部jackpot分成"],
        "代理jackpot分成": ["代理jackpot分成"],
        "jackpot贡献服务费": ["jackpot贡献服务费", "jackpot貢獻服務費"],
        "保险服务费": ["保险服务费", "保險服務費"],
        "带出": ["带出", "帶出"],
        "带入": ["带入", "帶入"],
        "联盟收益": ["联盟收益", "聯盟收益"],
        "俱乐部收益": ["俱乐部收益", "俱樂部收益"],
        "代理收益": ["代理收益"],
        "联盟服务费": ["联盟服务费", "聯盟服務費"],
        "俱乐部服务费": ["俱乐部服务费", "俱樂部服務費"],
        "代理服务费": ["代理服务费", "代理服務費"],
        "MTT ID": ["MTT ID", "MTTID"],
    }
    renamed = {}
    for std, variants in column_map.items():
        for var in variants:
            if var in df.columns:
                renamed[var] = std
                break
    df = df.rename(columns=renamed)
    return df

def detect_table_type(df):
    columns = df.columns.tolist()
    joined = ",".join(columns)
    if "下注量" in joined or "下注量" in columns:
        return "cowboy"
    elif "MTT ID" in columns or "比赛" in joined or "MTTID" in columns:
        return "mtt"
    elif "jackpot" in joined.lower():
        return "texas"
    return "unknown"

def check_texas_balance(df):
    df = normalize_columns(df)
    required = ["最终战绩", "总服务费", "保险", "jackpot贡献", "联盟jackpot分成", "俱乐部jackpot分成", "代理jackpot分成", "jackpot贡献服务费", "保险服务费", "牌局ID"]
    for col in required:
        if col not in df.columns:
            st.warning(f"缺少字段：{col}")
            return pd.DataFrame()
    grouped = df.groupby("牌局ID").agg({
        "最终战绩": "sum",
        "总服务费": "sum",
        "保险": "sum",
        "jackpot贡献": "sum",
        "联盟jackpot分成": "sum",
        "俱乐部jackpot分成": "sum",
        "代理jackpot分成": "sum",
        "jackpot贡献服务费": "sum",
        "保险服务费": "sum"
    })
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
    grouped = grouped[abs(grouped["差值"]) >= 0.001]
    grouped.reset_index(inplace=True)
    return grouped

def check_mtt_balance(df):
    df = normalize_columns(df)
    df["差值"] = df.get("总服务费", 0) - (
        df.get("联盟服务费", 0)
        + df.get("俱乐部服务费", 0)
        + df.get("代理服务费", 0)
    )
    df = df[abs(df["差值"]) >= 0.001]
    if df.empty:
        return df
    keep = ["MTT ID", "玩家昵称", "代理昵称", "俱乐部名称", "联盟名称", "差值"]
    return df[[c for c in keep if c in df.columns]]

def check_cowboy_balance(df):
    df = normalize_columns(df)
    results = []

    for _, row in df.iterrows():
        zhanji_diff = row.get("带出", 0) - row.get("带入", 0) - row.get("最终战绩", 0)
        fenrun_diff = row.get("最终战绩", 0) + row.get("联盟收益", 0) + row.get("俱乐部收益", 0) + row.get("代理收益", 0)

        if abs(zhanji_diff) >= 0.001:
            results.append({
                "类型": "战绩不平",
                "牌局ID": row.get("牌局ID", ""),
                "玩家昵称": row.get("玩家昵称", ""),
                "俱乐部名称": row.get("俱乐部名称", ""),
                "联盟名称": row.get("联盟名称", ""),
                "带出": row.get("带出", 0),
                "带入": row.get("带入", 0),
                "最终战绩": row.get("最终战绩", 0),
                "差值": zhanji_diff
            })
        if abs(fenrun_diff) >= 0.001:
            results.append({
                "类型": "分润不平",
                "牌局ID": row.get("牌局ID", ""),
                "玩家昵称": row.get("玩家昵称", ""),
                "俱乐部名称": row.get("俱乐部名称", ""),
                "联盟名称": row.get("联盟名称", ""),
                "最终战绩": row.get("最终战绩", 0),
                "联盟收益": row.get("联盟收益", 0),
                "俱乐部收益": row.get("俱乐部收益", 0),
                "代理收益": row.get("代理收益", 0),
                "差值": fenrun_diff
            })

    return pd.DataFrame(results)

st.title("联盟牌局平账校验工具")

uploaded_file = st.file_uploader("上传 Excel 导表文件", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    df.columns = df.columns.astype(str)

    table_type = detect_table_type(df)
    st.write(f"识别导表类型：**{table_type.upper()}**")

    if table_type == "texas":
        result = check_texas_balance(df)
    elif table_type == "cowboy":
        result = check_cowboy_balance(df)
    elif table_type == "mtt":
        result = check_mtt_balance(df)
    else:
        st.warning("未识别出导表类型，无法校验")
        result = pd.DataFrame()

    if not result.empty:
        st.subheader("不平账记录")
        st.dataframe(result)
        st.download_button("下载不平账记录", result.to_csv(index=False).encode("utf-8-sig"), file_name="不平账记录.csv", mime="text/csv")
    else:
        st.success("所有记录均为平账")

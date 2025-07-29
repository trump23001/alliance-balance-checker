
import streamlit as st
import pandas as pd

def detect_file_type(df):
    columns = set(df.columns.astype(str))
    zh = lambda *args: any(any(c in col for col in columns) for c in args)
    if zh('总服务费', '總服務費') and zh('Jackpot贡献', 'Jackpot貢獻'):
        return '德州类'
    elif zh('带入', '帶入') and zh('带出', '帶出'):
        return '牛仔类'
    elif zh('MTT ID') and zh('联盟服务费', '聯盟服務費'):
        return 'MTT类'
    return '未知'

def normalize_columns(df):
    return df.rename(columns=lambda col: str(col).strip().replace("總", "总").replace("貢獻", "贡献").replace("服務費", "服务费").replace("聯盟", "联盟").replace("俱樂部", "俱乐部").replace("代理", "代理"))

def check_texas(df):
    df = normalize_columns(df)
    required_cols = ['最终战绩', '总服务费', '保险', 'Jackpot贡献', '联盟jackpot分成', '俱乐部jackpot分成', '代理jackpot分成', 'Jackpot贡献服务费', '保险服务费', '牌局ID', '玩家昵称', '俱乐部名称', '联盟名称']
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        return False, f"缺少以下必要字段：{', '.join(missing)}", None

    df_numeric = df.copy()
    for col in required_cols:
        df_numeric[col] = pd.to_numeric(df_numeric[col], errors='coerce').fillna(0)

    df_numeric["是否平账"] = (
        df_numeric["最终战绩"] +
        df_numeric["总服务费"] +
        df_numeric["保险"] +
        df_numeric["Jackpot贡献"] +
        df_numeric["联盟jackpot分成"] +
        df_numeric["俱乐部jackpot分成"] +
        df_numeric["代理jackpot分成"] +
        df_numeric["Jackpot贡献服务费"] -
        df_numeric["保险服务费"]
    ).round(2)

    not_balanced = df_numeric[df_numeric["是否平账"] != 0]
    return True, "已完成平账校验", not_balanced

def check_niuzai(df):
    df = normalize_columns(df)
    required_cols = ['带入', '带出', '最终战绩', '联盟收益', '俱乐部收益', '代理收益', '牌局ID', '玩家昵称', '俱乐部名称', '联盟名称']
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        return False, f"缺少以下必要字段：{', '.join(missing)}", None

    df_numeric = df.copy()
    for col in required_cols:
        df_numeric[col] = pd.to_numeric(df_numeric[col], errors='coerce').fillna(0)

    df_numeric["战绩差值"] = df_numeric["带出"] - df_numeric["带入"] - df_numeric["最终战绩"]
    df_numeric["分润差值"] = (
        df_numeric["最终战绩"] +
        df_numeric["联盟收益"] +
        df_numeric["俱乐部收益"] +
        df_numeric["代理收益"]
    )

    not_balanced = df_numeric[(df_numeric["战绩差值"].round(2) != 0) | (df_numeric["分润差值"].round(2) != 0)]
    return True, "已完成平账校验", not_balanced

def check_mtt(df):
    df = normalize_columns(df)
    required_cols = ['总服务费', '联盟服务费', '俱乐部服务费', '代理服务费', 'MTT ID', '玩家昵称', '俱乐部名称', '联盟名称']
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        return False, f"缺少以下必要字段：{', '.join(missing)}", None

    df_numeric = df.copy()
    for col in required_cols:
        df_numeric[col] = pd.to_numeric(df_numeric[col], errors='coerce').fillna(0)

    df_numeric["分润差值"] = (
        df_numeric["总服务费"] -
        df_numeric["联盟服务费"] -
        df_numeric["俱乐部服务费"] -
        df_numeric["代理服务费"]
    ).round(2)

    not_balanced = df_numeric[df_numeric["分润差值"] != 0]
    return True, "已完成平账校验", not_balanced

st.title("牌局导表平账检测工具")
file = st.file_uploader("上传导出的 Excel 表格", type=["xlsx"])

if file:
    df = pd.read_excel(file)
    file_type = detect_file_type(df)
    st.write(f"检测到导表类型：**{file_type}**")

    if file_type == "德州类":
        ok, msg, result = check_texas(df)
    elif file_type == "牛仔类":
        ok, msg, result = check_niuzai(df)
    elif file_type == "MTT类":
        ok, msg, result = check_mtt(df)
    else:
        ok, msg, result = False, "未识别的导表格式，请检查字段或联系客服。", None

    if not ok:
        st.error(msg)
    elif result is not None and not result.empty:
        st.warning("以下记录存在不平账：")
        st.dataframe(result)
    else:
        st.success("全部记录均已平账 ✅")

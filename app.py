
import streamlit as st
import pandas as pd

st.set_page_config(page_title="联盟牌局平账校验工具", layout="wide")
st.title("联盟牌局平账校验工具（简繁体支持版）")

def detect_sheet_type(df):
    columns = set(df.columns)
    if any(col in columns for col in ['带入', '帶入']):
        return "Cowboy"
    elif any(col in columns for col in ['MTTID']):
        return "MTT"
    elif any(col in columns for col in ['最终战绩', '最終戰績']):
        return "Texas"
    return "Unknown"

field_map = {
    '牌局ID': ['牌局ID', '牌局Id', '局ID'],
    '最终战绩': ['最终战绩', '最終戰績'],
    '总服务费': ['总服务费', '總服務費'],
    '保险': ['保险', '保險'],
    'jackpot贡献': ['jackpot贡献', 'jackpot貢獻'],
    '联盟jackpot分成': ['联盟jackpot分成', '聯盟jackpot分成'],
    '俱乐部jackpot分成': ['俱乐部jackpot分成', '俱樂部jackpot分成'],
    '代理jackpot分成': ['代理jackpot分成'],
    'jackpot贡献服务费': ['jackpot贡献服务费', 'jackpot貢獻服務費'],
    '保险服务费': ['保险服务费', '保險服務費'],
    '带入': ['带入', '帶入'],
    '带出': ['带出', '帶出'],
    '联盟收益': ['联盟收益', '聯盟收益'],
    '俱乐部收益': ['俱乐部收益', '俱樂部收益'],
    '代理收益': ['代理收益'],
    '玩家昵称': ['玩家昵称', '玩家暱稱'],
    '俱乐部名称': ['俱乐部名称', '俱樂部名稱'],
    '联盟名称': ['联盟名称', '聯盟名稱'],
    'MTTID': ['MTTID'],
    '代理昵称': ['代理昵称', '代理暱稱'],
}

def normalize_columns(df, field_map):
    col_map = {}
    for std, variants in field_map.items():
        for var in variants:
            if var in df.columns:
                col_map[var] = std
                break
    return df.rename(columns=col_map)

def check_texas_balance(df):
    df = normalize_columns(df, field_map)
    df_grouped = df.groupby('牌局ID').sum(numeric_only=True)
    df_grouped['差值'] = df_grouped['最终战绩'] + df_grouped['总服务费'] + df_grouped['保险'] +                      df_grouped['jackpot贡献'] + df_grouped['联盟jackpot分成'] +                      df_grouped['俱乐部jackpot分成'] + df_grouped['代理jackpot分成'] +                      df_grouped['jackpot贡献服务费'] - df_grouped['保险服务费']
    result = df_grouped[abs(df_grouped['差值']) > 0.01].reset_index()
    return result

def check_cowboy_balance(df):
    df = normalize_columns(df, field_map)
    result_battle = df[abs(df['带出'] - df['带入'] - df['最终战绩']) > 0.01].copy()
    result_battle['差值'] = result_battle['带出'] - result_battle['带入'] - result_battle['最终战绩']
    result_profit = df[abs(df['最终战绩'] + df['联盟收益'] + df['俱乐部收益'] + df['代理收益']) > 0.01].copy()
    result_profit['差值'] = result_profit['最终战绩'] + df['联盟收益'] + df['俱乐部收益'] + df['代理收益']
    return result_battle, result_profit

def check_mtt_balance(df):
    df = normalize_columns(df, field_map)
    df['差值'] = df['总服务费'] - (df['联盟服务费'] + df['俱乐部服务费'] + df['代理服务费'])
    result = df[abs(df['差值']) > 0.01].copy()
    return result

uploaded_file = st.file_uploader("上传导出的 Excel 文件（.xlsx）", type=["xlsx", "xls"])
if uploaded_file:
    df = pd.read_excel(uploaded_file)
    sheet_type = detect_sheet_type(df)
    st.success(f"检测到导表类型为：**{sheet_type}**")
    if sheet_type == "Texas":
        result = check_texas_balance(df)
        st.write(f"共发现 {len(result)} 个不平账的牌局")
        st.dataframe(result)
    elif sheet_type == "Cowboy":
        res1, res2 = check_cowboy_balance(df)
        st.write(f"战绩不平账玩家数量：{len(res1)}")
        st.dataframe(res1)
        st.write(f"分润不平账玩家数量：{len(res2)}")
        st.dataframe(res2)
    elif sheet_type == "MTT":
        result = check_mtt_balance(df)
        st.write(f"共发现 {len(result)} 条不平账记录")
        st.dataframe(result)
    else:
        st.warning("无法识别该导表类型，请检查表头字段。")

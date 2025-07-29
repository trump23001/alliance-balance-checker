
import streamlit as st
import pandas as pd
import numpy as np
import chardet

def detect_encoding(file):
    raw_data = file.read()
    file.seek(0)
    return chardet.detect(raw_data)['encoding']

# 繁简字段映射
FIELD_MAP = {
    '德州': {
        '最终战绩': ['最终战绩', '最終戰績'],
        '总服务费': ['总服务费', '總服務費'],
        '保险': ['保险', '保險'],
        'jackpot贡献': ['jackpot贡献', 'jackpot貢獻'],
        '联盟jackpot分成': ['联盟jackpot分成', '聯盟jackpot分成'],
        '俱乐部jackpot分成': ['俱乐部jackpot分成', '俱樂部jackpot分成'],
        '代理jackpot分成': ['代理jackpot分成'],
        'jackpot贡献服务费': ['jackpot贡献服务费', 'jackpot貢獻服務費'],
        '保险服务费': ['保险服务费', '保險服務費'],
        '牌局ID': ['牌局ID']
    },
    '牛仔': {
        '带出': ['带出', '帶出'],
        '带入': ['带入', '帶入'],
        '最终战绩': ['最终战绩', '最終戰績'],
        '联盟收益': ['联盟收益', '聯盟收益'],
        '俱乐部收益': ['俱乐部收益', '俱樂部收益'],
        '代理收益': ['代理收益'],
        '牌局ID': ['牌局ID'],
        '玩家昵称': ['玩家昵称'],
        '俱乐部名称': ['俱乐部名称'],
        '联盟名称': ['联盟名称']
    },
    'MTT': {
        '总服务费': ['总服务费', '總服務費'],
        '联盟服务费': ['联盟服务费', '聯盟服務費'],
        '俱乐部服务费': ['俱乐部服务费', '俱樂部服務費'],
        '代理服务费': ['代理服务费'],
        'MTT ID': ['MTT ID'],
        '玩家昵称': ['玩家昵称'],
        '俱乐部名称': ['俱乐部名称'],
        '联盟名称': ['联盟名称'],
        '代理昵称': ['代理昵称']
    }
}

def identify_game_type(df):
    columns = df.columns.tolist()
    if any('MTT' in str(c) or '比赛' in str(c) for c in columns):
        return 'MTT'
    if any('下注量' in str(c) for c in columns):
        return '牛仔'
    if any('jackpot' in str(c).lower() for c in columns):
        return '德州'
    return '未知'

def standardize_columns(df, game_type):
    mapping = FIELD_MAP[game_type]
    col_map = {}
    for std, variants in mapping.items():
        for v in variants:
            if v in df.columns:
                col_map[v] = std
    df = df.rename(columns=col_map)
    return df

def check_texas_balance(df):
    df = standardize_columns(df, '德州')
    if not all(k in df.columns for k in FIELD_MAP['德州']):
        return pd.DataFrame()
    df_grouped = df.groupby('牌局ID').agg({
        '最终战绩': 'sum',
        '总服务费': 'sum',
        '保险': 'sum',
        'jackpot贡献': 'sum',
        '联盟jackpot分成': 'sum',
        '俱乐部jackpot分成': 'sum',
        '代理jackpot分成': 'sum',
        'jackpot贡献服务费': 'sum',
        '保险服务费': 'sum'
    }).reset_index()
    df_grouped['差值'] = df_grouped['最终战绩'] + df_grouped['总服务费'] + df_grouped['保险'] + df_grouped['jackpot贡献'] + df_grouped['联盟jackpot分成'] + df_grouped['俱乐部jackpot分成'] + df_grouped['代理jackpot分成'] + df_grouped['jackpot贡献服务费'] - df_grouped['保险服务费']
    df_grouped = df_grouped[df_grouped['差值'].abs() > 0.01]
    return df_grouped

def check_mtt_balance(df):
    df = standardize_columns(df, 'MTT')
    if not all(k in df.columns for k in FIELD_MAP['MTT']):
        return pd.DataFrame()
    df['差值'] = df['总服务费'] - (df['联盟服务费'] + df['俱乐部服务费'] + df['代理服务费'])
    df = df[df['差值'].abs() > 0.01]
    return df[['MTT ID', '玩家昵称', '俱乐部名称', '联盟名称', '代理昵称', '差值']]

def check_cowboy_balance(df):
    df = standardize_columns(df, '牛仔')
    required = FIELD_MAP['牛仔']
    if not all(k in df.columns for k in required):
        return pd.DataFrame(), pd.DataFrame()
    df['战绩差值'] = df['带出'] - df['带入'] - df['最终战绩']
    df['分润差值'] = df['最终战绩'] + df['联盟收益'] + df['俱乐部收益'] + df['代理收益']
    df1 = df[df['战绩差值'].abs() > 0.01]
    df2 = df[df['分润差值'].abs() > 0.01]
    return df1[['牌局ID', '玩家昵称', '俱乐部名称', '联盟名称', '带出', '带入', '最终战绩', '战绩差值']], df2[['牌局ID', '玩家昵称', '俱乐部名称', '联盟名称', '最终战绩', '联盟收益', '俱乐部收益', '代理收益', '分润差值']]

st.title("联盟平账检测工具")

uploaded_file = st.file_uploader("请上传导出的Excel表格", type=["xlsx"])
if uploaded_file:
    encoding = detect_encoding(uploaded_file)
    df = pd.read_excel(uploaded_file)
    game_type = identify_game_type(df)
    st.info(f"检测到导表类型为：{game_type}")

    if game_type == '德州':
        result = check_texas_balance(df)
        if result.empty:
            st.success("所有牌局均平账")
        else:
            st.warning(f"共 {len(result)} 个不平账牌局")
            st.dataframe(result)
            st.download_button("下载不平账结果", result.to_excel(index=False), "texas_balance_issues.xlsx")

    elif game_type == 'MTT':
        result = check_mtt_balance(df)
        if result.empty:
            st.success("MTT数据平账无误")
        else:
            st.warning(f"共 {len(result)} 个不平账记录")
            st.dataframe(result)
            st.download_button("下载不平账结果", result.to_excel(index=False), "mtt_balance_issues.xlsx")

    elif game_type == '牛仔':
        res1, res2 = check_cowboy_balance(df)
        if res1.empty and res2.empty:
            st.success("牛仔数据全部平账")
        else:
            if not res1.empty:
                st.subheader("战绩不平账记录")
                st.dataframe(res1)
                st.download_button("下载战绩不平账", res1.to_excel(index=False), "cowboy_result_issues.xlsx")
            if not res2.empty:
                st.subheader("分润不平账记录")
                st.dataframe(res2)
                st.download_button("下载分润不平账", res2.to_excel(index=False), "cowboy_profit_issues.xlsx")

    else:
        st.error("未能识别导表类型，请确认文件内容")

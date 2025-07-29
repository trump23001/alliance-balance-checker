
import streamlit as st
import pandas as pd
import numpy as np
import io

def detect_file_type(df):
    headers = df.columns.tolist()
    joined_headers = ''.join(headers)
    if any(x in joined_headers for x in ['MTT', '比赛']):
        return 'MTT'
    elif any('下注量' in x for x in headers):
        return 'Cowboy'
    elif any('jackpot' in x.lower() for x in headers):
        return 'Texas'
    return 'Unknown'

def check_texas_balance(df):
    df = df.copy()
    required_columns = [
        '牌局ID', '最终战绩', '总服务费', '保险', 'Jackpot贡献',
        '联盟Jackpot分成', '俱乐部Jackpot分成', '代理Jackpot分成',
        'Jackpot贡献服务费', '保险服务费'
    ]
    df = df[[col for col in required_columns if col in df.columns]]
    df_grouped = df.groupby('牌局ID').sum().reset_index()
    df_grouped['差值'] = df_grouped['最终战绩'] + df_grouped['总服务费'] + df_grouped['保险'] + df_grouped['Jackpot贡献'] + df_grouped['联盟Jackpot分成'] + df_grouped['俱乐部Jackpot分成'] + df_grouped['代理Jackpot分成'] + df_grouped['Jackpot贡献服务费'] - df_grouped['保险服务费']
    df_grouped = df_grouped[np.abs(df_grouped['差值']) > 0.01]
    return df_grouped

def check_cowboy_balance(df):
    df = df.copy()
    df['战绩差值'] = df['带出'] - df['带入'] - df['最终战绩']
    df['分润差值'] = df['最终战绩'] + df['联盟收益'] + df['俱乐部收益'] + df['代理收益']

    result1 = df[np.abs(df['战绩差值']) > 0.01][['牌局ID', '玩家昵称', '俱乐部名称', '联盟名称', '带出', '带入', '最终战绩', '战绩差值']]
    result2 = df[np.abs(df['分润差值']) > 0.01][['牌局ID', '玩家昵称', '俱乐部名称', '联盟名称', '最终战绩', '联盟收益', '俱乐部收益', '代理收益', '分润差值']]
    return result1, result2

def check_mtt_balance(df):
    df = df.copy()
    df['差值'] = df['总服务费'] - df['联盟服务费'] - df['俱乐部服务费'] - df['代理服务费']
    result = df[np.abs(df['差值']) > 0.01][['MTTID', '玩家昵称', '代理昵称', '俱乐部名称', '联盟名称', '差值']]
    return result

st.title("导表平账判定工具")

uploaded_file = st.file_uploader("上传导出表（支持德州/牛仔/MTT）", type=["xls", "xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    game_type = detect_file_type(df)
    st.write(f"检测到导表类型为：**{game_type}**")

    if game_type == 'Texas':
        result = check_texas_balance(df)
        if result.empty:
            st.success("所有德州类牌局平账✅")
        else:
            st.warning(f"共 {len(result)} 个德州类牌局不平账")
            st.dataframe(result)
            st.download_button("下载不平账结果", data=result.to_excel(index=False), file_name="德州不平账.xlsx")

    elif game_type == 'Cowboy':
        result1, result2 = check_cowboy_balance(df)
        if result1.empty and result2.empty:
            st.success("所有牛仔类牌局平账✅")
        else:
            if not result1.empty:
                st.warning("战绩不平账记录：")
                st.dataframe(result1)
                st.download_button("下载战绩不平账结果", data=result1.to_excel(index=False), file_name="牛仔战绩不平账.xlsx")
            if not result2.empty:
                st.warning("分润不平账记录：")
                st.dataframe(result2)
                st.download_button("下载分润不平账结果", data=result2.to_excel(index=False), file_name="牛仔分润不平账.xlsx")

    elif game_type == 'MTT':
        result = check_mtt_balance(df)
        if result.empty:
            st.success("所有MTT类牌局平账✅")
        else:
            st.warning(f"共 {len(result)} 个MTT玩家记录不平账")
            st.dataframe(result)
            st.download_button("下载MTT不平账结果", data=result.to_excel(index=False), file_name="MTT不平账.xlsx")

    else:
        st.error("未识别的导表类型，请检查文件内容")

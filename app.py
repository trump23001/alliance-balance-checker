
import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Balance Checker", layout="wide")

# 字段映射表
FIELD_MAP = {
    '最终战绩': ['最终战绩', '最終戰績'],
    '总服务费': ['总服务费', '總服務費'],
    '保险': ['保险', '保險'],
    'jackpot贡献': ['jackpot贡献', 'jackpot貢獻'],
    '联盟jackpot分成': ['联盟jackpot分成', '聯盟jackpot分成'],
    '俱乐部jackpot分成': ['俱乐部jackpot分成', '俱樂部jackpot分成'],
    '代理jackpot分成': ['代理jackpot分成', '代理jackpot分成'],
    'jackpot贡献服务费': ['jackpot贡献服务费', 'jackpot貢獻服務費'],
    '保险服务费': ['保险服务费', '保險服務費'],
    '带入': ['带入', '帶入'],
    '带出': ['带出', '帶出'],
    '联盟收益': ['联盟收益', '聯盟收益'],
    '俱乐部收益': ['俱乐部收益', '俱樂部收益'],
    '代理收益': ['代理收益', '代理收益'],
    '联盟服务费': ['联盟服务费', '聯盟服務費'],
    '俱乐部服务费': ['俱乐部服务费', '俱樂部服務費'],
    '代理服务费': ['代理服务费', '代理服務費']
}

# 自动字段映射函数
def map_fields(df):
    df_columns = df.columns.tolist()
    mapped = {}
    for key, aliases in FIELD_MAP.items():
        for alias in aliases:
            if alias in df_columns:
                mapped[key] = alias
                break
    return mapped

# 文件类型判断
def detect_file_type(df):
    columns = df.columns.tolist()
    if any('比赛' in str(col) or 'MTT' in str(col).upper() for col in columns):
        return 'mtt'
    elif any('下注' in str(col) or '下注量' in str(col) for col in columns):
        return 'cowboy'
    elif any('jackpot' in str(col).lower() for col in columns):
        return 'texas'
    return 'unknown'

# 平账逻辑
def check_texas(df, fmap):
    df_grouped = df.groupby(df.columns[0]).agg({fmap[k]: 'sum' for k in fmap if k in [
        '最终战绩', '总服务费', '保险', 'jackpot贡献', '联盟jackpot分成', '俱乐部jackpot分成',
        '代理jackpot分成', 'jackpot贡献服务费', '保险服务费'
    ]})
    df_grouped['差值'] = df_grouped[fmap['最终战绩']] + df_grouped[fmap['总服务费']] + df_grouped[fmap['保险']] +                      df_grouped[fmap['jackpot贡献']] + df_grouped[fmap['联盟jackpot分成']] +                      df_grouped[fmap['俱乐部jackpot分成']] + df_grouped[fmap['代理jackpot分成']] +                      df_grouped[fmap['jackpot贡献服务费']] - df_grouped[fmap['保险服务费']]
    df_grouped = df_grouped[df_grouped['差值'].abs() > 1e-6]
    return df_grouped.reset_index()

def check_cowboy(df, fmap):
    df['战绩差值'] = df[fmap['带出']] - df[fmap['带入']] - df[fmap['最终战绩']]
    df['分润差值'] = df[fmap['最终战绩']] + df[fmap['联盟收益']] + df[fmap['俱乐部收益']] + df[fmap['代理收益']]
    df1 = df[df['战绩差值'].abs() > 1e-6]
    df2 = df[df['分润差值'].abs() > 1e-6]
    return df1, df2

def check_mtt(df, fmap):
    df['差值'] = df[fmap['总服务费']] - df[fmap['联盟服务费']] - df[fmap['俱乐部服务费']] - df[fmap['代理服务费']]
    return df[df['差值'].abs() > 1e-6]

# Streamlit主逻辑
st.title("联盟导表平账校验工具")

uploaded_file = st.file_uploader("请上传导出表格文件 (.xlsx)", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    file_type = detect_file_type(df)
    fmap = map_fields(df)
    st.success(f"识别为：{file_type.upper()} 表格")

    if file_type == 'texas':
        result = check_texas(df, fmap)
        if not result.empty:
            st.error("存在不平账牌局：")
            st.dataframe(result)
            towrite = io.BytesIO()
            result.to_excel(towrite, index=False)
            st.download_button("📥 下载不平账结果", towrite.getvalue(), file_name="texas_unbalanced.xlsx")
        else:
            st.success("全部平账 ✅")

    elif file_type == 'cowboy':
        df1, df2 = check_cowboy(df, fmap)
        if not df1.empty:
            st.error("存在战绩不平账：")
            st.dataframe(df1)
        if not df2.empty:
            st.error("存在分润不平账：")
            st.dataframe(df2)
        if df1.empty and df2.empty:
            st.success("全部平账 ✅")

    elif file_type == 'mtt':
        result = check_mtt(df, fmap)
        if not result.empty:
            st.error("存在服务费不平账：")
            st.dataframe(result)
        else:
            st.success("全部平账 ✅")

    else:
        st.warning("未能识别导表类型")

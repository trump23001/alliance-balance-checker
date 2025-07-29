
import pandas as pd

def check_texas(df):
    df = df.copy()
    numeric_cols = [
        "最终战绩", "总服务费", "保险", "jackpot贡献", "联盟jackpot分成",
        "俱乐部jackpot分成", "代理jackpot分成", "jackpot贡献服务费", "保险服务费"
    ]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df.get(col, 0), errors='coerce').fillna(0)

    df["平账校验值"] = df["最终战绩"] + df["总服务费"] + df["保险"] + df["jackpot贡献"] +                   df["联盟jackpot分成"] + df["俱乐部jackpot分成"] + df["代理jackpot分成"] +                   df["jackpot贡献服务费"] - df["保险服务费"]

    result = df[df["平账校验值"].abs() > 0.01].copy()
    result["差值"] = result["平账校验值"]
    return result[["牌局ID", "玩家昵称", "俱乐部名称", "联盟名称", "差值"]], result

def check_cowboy(df):
    df = df.copy()
    numeric_cols = ["带入", "带出", "最终战绩", "联盟收益", "俱乐部收益", "代理收益"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df.get(col, 0), errors='coerce').fillna(0)

    df["战绩是否平账"] = df["带出"] - df["带入"] - df["最终战绩"]
    df["分润是否平账"] = df["最终战绩"] + df["联盟收益"] + df["俱乐部收益"] + df["代理收益"]

    result = df[(df["战绩是否平账"].abs() > 0.01) | (df["分润是否平账"].abs() > 0.01)].copy()
    result["差值"] = result["战绩是否平账"] + result["分润是否平账"]

    return result[["牌局ID", "玩家昵称", "俱乐部名称", "联盟名称", "带入", "带出", "最终战绩", "差值"]], result

def check_mtt(df):
    df = df.copy()
    numeric_cols = ["总服务费", "联盟服务费", "俱乐部服务费", "代理服务费"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df.get(col, 0), errors='coerce').fillna(0)

    df["是否平账"] = df["总服务费"] - df["联盟服务费"] - df["俱乐部服务费"] - df["代理服务费"]
    result = df[df["是否平账"].abs() > 0.01].copy()
    result["差值"] = result["是否平账"]
    return result[["MTT ID", "玩家昵称", "俱乐部名称", "联盟名称", "代理昵称", "差值"]], result

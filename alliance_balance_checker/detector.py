
def detect_sheet_type(df):
    lower_cols = [str(c).lower() for c in df.columns]

    if any("mtt" in c or "比赛" in c for c in lower_cols):
        return "MTT类"
    elif any("下注" in c for c in lower_cols):
        return "牛仔类"
    elif any("jackpot" in c.lower() for c in df.columns):
        return "德州类"
    else:
        return "未知"

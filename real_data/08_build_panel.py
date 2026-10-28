# -*- coding: utf-8 -*-
"""Assemble the real firm-quarter panel from downloaded statements, valuations and TDDI."""
import os
import glob
import numpy as np
import pandas as pd
from scipy.stats.mstats import winsorize

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(BASE, "real_data", "raw")
OUT = os.path.join(BASE, "real_data")

SAMPLE = pd.read_csv(os.path.join(OUT, "sample_codes.csv"), dtype={"SECURITY_CODE": str})
SAMPLE["SECURITY_CODE"] = SAMPLE["SECURITY_CODE"].str.zfill(6)
CODES = set(SAMPLE["SECURITY_CODE"])


def read_balance():
    frames = []
    for f in glob.glob(os.path.join(RAW, "balance_*.csv")):
        df = pd.read_csv(f, dtype={"SECURITY_CODE": str})
        frames.append(df)
    df = pd.concat(frames, ignore_index=True)
    df["code"] = df["SECURITY_CODE"].str.zfill(6)
    df["date"] = pd.to_datetime(df["REPORT_DATE"]).dt.normalize()
    df = df[df["code"].isin(CODES)].drop_duplicates(["code", "date"])
    return df[["code", "date", "INDUSTRY_NAME", "TOTAL_ASSETS", "TOTAL_LIABILITIES",
               "TOTAL_EQUITY", "MONETARYFUNDS"]]


def read_income():
    frames = []
    for f in glob.glob(os.path.join(RAW, "income_*.csv")):
        df = pd.read_csv(f, dtype={"SECURITY_CODE": str})
        frames.append(df)
    df = pd.concat(frames, ignore_index=True)
    df["code"] = df["SECURITY_CODE"].str.zfill(6)
    df["date"] = pd.to_datetime(df["REPORT_DATE"]).dt.normalize()
    df = df[df["code"].isin(CODES)].drop_duplicates(["code", "date"])
    return df[["code", "date", "TOTAL_OPERATE_INCOME", "OPERATE_COST", "SALE_EXPENSE",
               "MANAGE_EXPENSE", "OPERATE_PROFIT", "PARENT_NETPROFIT"]]


def read_valuation():
    frames = []
    for f in glob.glob(os.path.join(RAW, "valuation_*.csv")):
        df = pd.read_csv(f, dtype={"SECURITY_CODE": str})
        frames.append(df)
    df = pd.concat(frames, ignore_index=True)
    df["code"] = df["SECURITY_CODE"].str.zfill(6)
    df["trade_date"] = pd.to_datetime(df["TRADE_DATE"]).dt.normalize()
    df["date"] = df["trade_date"].dt.to_period("Q").dt.end_time.dt.normalize()
    df = df[df["code"].isin(CODES)].drop_duplicates(["code", "date"])
    return df[["code", "date", "TOTAL_MARKET_CAP", "PB_MRQ", "CLOSE_PRICE"]]


def to_quarterly(df):
    """Convert year-to-date cumulative income items to single-quarter flows."""
    df = df.sort_values(["code", "date"]).copy()
    df["year"] = df["date"].dt.year
    df["q"] = df["date"].dt.quarter
    cum = ["TOTAL_OPERATE_INCOME", "OPERATE_COST", "SALE_EXPENSE",
           "MANAGE_EXPENSE", "OPERATE_PROFIT", "PARENT_NETPROFIT"]
    for c in cum:
        q = df.groupby(["code", "year"])[c].diff()
        q = q.where(df["q"] != 1, df[c])
        df[c + "_Q"] = q
    return df


def winsor(s, lo=0.01, hi=0.01):
    a = np.array(pd.to_numeric(s, errors="coerce"), dtype=float, copy=True)
    m = np.isfinite(a)
    if m.sum() < 20:
        return s
    a[m] = winsorize(a[m], limits=[lo, hi])
    return pd.Series(a, index=s.index)


def main():
    bal = read_balance()
    inc = read_income()
    val = read_valuation()

    inc = to_quarterly(inc)
    df = bal.merge(inc, on=["code", "date"], how="outer")
    df = df.merge(val, on=["code", "date"], how="left")
    df = df.sort_values(["code", "date"])

    df["assets"] = df["TOTAL_ASSETS"]
    df["liab"] = df["TOTAL_LIABILITIES"]
    df["equity"] = df["TOTAL_EQUITY"]
    df["cash"] = df["MONETARYFUNDS"]
    df["revenue"] = df["TOTAL_OPERATE_INCOME_Q"]
    df["cogs"] = df["OPERATE_COST_Q"]
    df["sale_exp"] = df["SALE_EXPENSE_Q"]
    df["admin_exp"] = df["MANAGE_EXPENSE_Q"]
    df["op_profit"] = df["OPERATE_PROFIT_Q"]
    df["net_profit"] = df["PARENT_NETPROFIT_Q"]

    df["mcap"] = df["TOTAL_MARKET_CAP"]
    # Fallback: market cap from PB and book equity when the quote is missing.
    df["mcap"] = df["mcap"].fillna(df["PB_MRQ"] * df["equity"])
    df["mcap"] = df["mcap"].fillna(df["CLOSE_PRICE"] * np.nan)

    df["tobins_q"] = (df["mcap"] + df["liab"]) / df["assets"]
    df["log_q"] = np.log(df["tobins_q"].where(df["tobins_q"] > 0))
    df["mb"] = df["mcap"] / df["equity"]
    df["log_mcap"] = np.log(df["mcap"].where(df["mcap"] > 0))
    df["ev_assets"] = df["tobins_q"]
    df["roa"] = df["net_profit"] / df["assets"]
    df["assets_lag"] = df.groupby("code")["assets"].shift(1)
    df["roa_avg"] = df["net_profit"] / ((df["assets"] + df["assets_lag"]) / 2)
    df["sales_ratio"] = df["sale_exp"] / df["revenue"]
    df["admin_ratio"] = df["admin_exp"] / df["revenue"]
    df["period_ratio"] = (df["sale_exp"] + df["admin_exp"]) / df["revenue"]
    df["gross_margin"] = (df["revenue"] - df["cogs"]) / df["revenue"]
    df["op_margin"] = df["op_profit"] / df["revenue"]
    df["rev_growth"] = df["revenue"] / df.groupby("code")["revenue"].shift(4) - 1
    df["size"] = np.log(df["assets"].where(df["assets"] > 0))
    df["leverage"] = df["liab"] / df["assets"]
    df["cash_ratio"] = df["cash"] / df["assets"]
    df["asset_turnover"] = df["revenue"] / df["assets"]

    tddi = pd.read_csv(os.path.join(OUT, "tddi.csv"), dtype={"code": str})
    tddi["code"] = tddi["code"].str.zfill(6)
    df = df.merge(tddi[["code", "tddi", "tddi_narrow", "fpdci", "generic_digital",
                        "app_exposure"]], on="code", how="left")
    consumer_inds = ["广告营销", "游戏Ⅱ", "互联网电商", "数字媒体", "影视院线",
                     "出版", "电视广播Ⅱ", "教育"]
    df["consumer"] = df["INDUSTRY_NAME"].isin(consumer_inds).astype(int)

    # Reference quarter for treatment timing.
    df["post"] = (df["date"] >= pd.Timestamp("2021-06-30")).astype(int)
    df["post_pipl"] = (df["date"] >= pd.Timestamp("2021-12-31")).astype(int)
    df["post_x_tddi"] = df["post"] * df["tddi"]
    df["post_x_narrow"] = df["post"] * df["tddi_narrow"]
    df["pipl_x_tddi"] = df["post_pipl"] * df["tddi"]
    # Firm-level tercile split (top third vs the rest) for the binary DiD.
    firm_tddi = df.groupby("code")["tddi"].first()
    q2 = firm_tddi.quantile(2 / 3)
    df["high_tddi"] = (df["tddi"] >= q2).astype(int)
    df["post_high"] = df["post"] * df["high_tddi"]
    df["pipl_high"] = df["post_pipl"] * df["high_tddi"]
    firm_narrow = df.groupby("code")["tddi_narrow"].first()
    qn = firm_narrow.quantile(2 / 3)
    df["high_narrow"] = (df["tddi_narrow"] >= qn).astype(int)
    df["post_high_narrow"] = df["post"] * df["high_narrow"]

    df = df[(df["date"] >= pd.Timestamp("2018-03-31")) &
            (df["date"] <= pd.Timestamp("2023-12-31"))].copy()
    df = df[df["assets"] > 0].copy()
    df = df[df["revenue"] > 0].copy()
    df = df[df["tddi"].notna()].copy()

    ratio_vars = ["tobins_q", "log_q", "mb", "roa", "roa_avg", "sales_ratio",
                  "admin_ratio", "period_ratio", "gross_margin", "op_margin",
                  "rev_growth", "size", "leverage", "cash_ratio", "asset_turnover"]
    for c in ratio_vars:
        df[c] = winsor(df[c])

    # Drop implausible accounting values after winsorisation.
    df = df[df["tobins_q"] > 0].copy()
    df["log_q"] = np.log(df["tobins_q"])

    df["yq"] = df["date"].dt.to_period("Q").astype(str)
    df["ind_q"] = df["INDUSTRY_NAME"].astype(str) + "_" + df["yq"]
    df["firm_id"] = df["code"]

    cols = ["code", "firm_id", "date", "yq", "INDUSTRY_NAME", "ind_q", "assets", "liab",
            "equity", "cash", "revenue", "cogs", "sale_exp", "admin_exp", "op_profit",
            "net_profit", "mcap", "tobins_q", "log_q", "mb", "log_mcap", "roa", "roa_avg",
            "sales_ratio", "admin_ratio", "period_ratio", "gross_margin", "op_margin",
            "rev_growth", "size", "leverage", "cash_ratio", "asset_turnover",
            "tddi", "tddi_narrow", "fpdci", "generic_digital", "app_exposure",
            "consumer", "high_tddi", "high_narrow", "post", "post_pipl",
            "post_x_tddi", "post_x_narrow", "post_high", "post_high_narrow",
            "pipl_x_tddi", "pipl_high"]
    panel = df[cols].copy()
    panel.to_csv(os.path.join(OUT, "panel.csv"), index=False, encoding="utf-8-sig")
    print("panel", panel.shape)
    print("firms", panel["code"].nunique(), "quarters", panel["date"].nunique())
    print(panel.groupby("post").size().to_string())

    desc = panel[["tobins_q", "roa", "sales_ratio", "gross_margin", "op_margin",
                  "rev_growth", "size", "leverage", "cash_ratio", "tddi",
                  "tddi_narrow", "fpdci", "generic_digital"]].describe().T
    desc.to_csv(os.path.join(OUT, "desc_stats.csv"), encoding="utf-8-sig")
    print(desc.round(3).to_string())


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""Daily event study around Apple ATT (and placebo dates)."""
import os
import glob
import numpy as np
import pandas as pd
import statsmodels.api as sm

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(BASE, "real_data", "raw", "prices")
OUT = os.path.join(BASE, "real_outputs")
os.makedirs(OUT, exist_ok=True)


def load_returns():
    frames = []
    for f in glob.glob(os.path.join(RAW, "*.csv")):
        code = os.path.splitext(os.path.basename(f))[0]
        if code.startswith("index_"):
            continue
        df = pd.read_csv(f)
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date")
        df["ret"] = df["close"].pct_change()
        df["code"] = code
        frames.append(df[["code", "date", "ret"]])
    return pd.concat(frames, ignore_index=True)


def load_index():
    for tag in ["index_hs300", "index_csi500"]:
        f = os.path.join(RAW, tag + ".csv")
        if os.path.exists(f):
            df = pd.read_csv(f)
            df["date"] = pd.to_datetime(df["date"])
            df = df.sort_values("date")
            df["mkt"] = df["close"].pct_change()
            return df[["date", "mkt"]]
    raise FileNotFoundError("no index file")


def car_one(g, mkt, event_date, win=(1, 1)):
    g = g.dropna(subset=["ret"]).merge(mkt, on="date", how="inner")
    g = g.sort_values("date").reset_index(drop=True)
    idx = g.index[g["date"] >= pd.Timestamp(event_date)]
    if len(idx) == 0:
        return np.nan
    e = idx[0]
    est = g.iloc[max(0, e - 250):max(0, e - 30)]
    if len(est) < 80:
        return np.nan
    X = sm.add_constant(est["mkt"].to_numpy())
    try:
        beta = np.linalg.lstsq(X, est["ret"].to_numpy(), rcond=None)[0]
    except Exception:
        return np.nan
    a, b = beta
    ev = g.iloc[max(0, e - win[0]):min(len(g), e + win[1] + 1)]
    ar = ev["ret"].to_numpy() - (a + b * ev["mkt"].to_numpy())
    return float(np.nansum(ar))


def run_event(df, mkt, event_date, win=(1, 1)):
    rows = []
    for code, g in df.groupby("code"):
        rows.append({"code": code, "car": car_one(g, mkt, event_date, win)})
    out = pd.DataFrame(rows)
    return out


def main():
    df = load_returns()
    mkt = load_index()
    events = {
        "ATT_2021-04-27": ("2021-04-27", (1, 1)),
        "ATT_announce_2020-06-23": ("2020-06-23", (1, 1)),
        "PIPL_2021-08-23": ("2021-08-23", (1, 1)),
        "PIPL_effective_2021-11-01": ("2021-11-01", (1, 1)),
    }
    all_car = []
    for name, (dt, win) in events.items():
        c = run_event(df, mkt, dt, win)
        c["event"] = name
        all_car.append(c)
    car = pd.concat(all_car, ignore_index=True)
    car.to_csv(os.path.join(OUT, "car.csv"), index=False, encoding="utf-8-sig")
    print(car.groupby("event")["car"].describe().to_string())

    # placebo distribution of the TDDI coefficient on 100 random dates
    panel = pd.read_csv(os.path.join(BASE, "real_data", "panel.csv"),
                        dtype={"code": str})
    tddi = panel.groupby("code")["tddi"].first()
    rng = np.random.default_rng(20260610)
    dates = pd.to_datetime(sorted(df["date"].unique()))
    candidates = dates[(dates >= "2019-02-01") & (dates <= "2022-11-30")]
    rows = []
    for _ in range(100):
        dt = pd.Timestamp(rng.choice(candidates))
        c = run_event(df, mkt, dt, (1, 1)).set_index("code")
        c["tddi"] = tddi
        d = c.dropna()
        if len(d) < 30:
            continue
        X = sm.add_constant(d[["tddi"]])
        r = sm.OLS(d["car"], X).fit(cov_type="HC1")
        rows.append({"date": dt, "b": float(r.params["tddi"]),
                     "t": float(r.tvalues["tddi"]), "n": int(r.nobs)})
    pl = pd.DataFrame(rows)
    pl.to_csv(os.path.join(OUT, "car_placebo.csv"), index=False, encoding="utf-8-sig")
    print(pl["b"].describe().to_string())


if __name__ == "__main__":
    main()

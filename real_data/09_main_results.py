# -*- coding: utf-8 -*-
"""Main real-data results: binary high-TDDI DiD, event study, mechanisms, robustness."""
import os
import json
import warnings
import numpy as np
import pandas as pd
from linearmodels.panel import PanelOLS
from scipy.stats import chi2

warnings.filterwarnings("ignore")

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "real_outputs")
os.makedirs(OUT, exist_ok=True)

CONTROLS = ["size", "leverage", "cash_ratio"]
OUTCOMES = ["log_q", "tobins_q", "gross_margin", "roa", "sales_ratio",
            "period_ratio", "op_margin", "rev_growth"]


def load_panel():
    df = pd.read_csv(os.path.join(BASE, "real_data", "panel.csv"),
                     dtype={"code": str})
    df["date"] = pd.to_datetime(df["date"])
    df["year"] = df["date"].dt.year
    df["quarter"] = df["date"].dt.quarter
    df["event_time"] = (df["year"] - 2021) * 4 + (df["quarter"] - 2)
    df["post3"] = (df["date"] >= pd.Timestamp("2021-09-30")).astype(int)
    df["post3_high"] = df["post3"] * df["high_tddi"]
    df["post3_high_narrow"] = df["post3"] * df["high_narrow"]
    df["post3_x_tddi"] = df["post3"] * df["tddi"]
    df["post3_x_narrow"] = df["post3"] * df["tddi_narrow"]
    df["post3_x_generic"] = df["post3"] * df["generic_digital"]
    df["fpdci_high"] = (df["fpdci"] > df["fpdci"].median()).astype(int)
    df["app_high"] = (df["app_exposure"] > df["app_exposure"].median()).astype(int)
    return df


def stars(p):
    return "***" if p < 0.01 else "**" if p < 0.05 else "*" if p < 0.1 else ""


def est(df, y, xvars, indq=True, cluster_time=False):
    d = df.dropna(subset=[y] + xvars).copy()
    if d["firm_id"].nunique() < 10:
        return None
    d = d.set_index(["firm_id", "date"])
    other = d[["ind_q"]] if indq else None
    mod = PanelOLS(d[y], d[xvars], entity_effects=True,
                   time_effects=not indq, other_effects=other,
                   drop_absorbed=True)
    kw = dict(cov_type="clustered", cluster_entity=True)
    if cluster_time:
        kw["cluster_time"] = True
    return mod.fit(**kw)


def pack(res, key):
    if res is None:
        return None
    b = float(res.params.get(key, np.nan))
    se = float(res.std_errors.get(key, np.nan))
    p = float(res.pvalues.get(key, np.nan))
    return {"b": b, "se": se, "p": p, "t": b / se if se else np.nan,
            "n": int(res.nobs), "r2": float(res.rsquared), "stars": stars(p)}


def binary_baseline(df):
    out = {}
    for y in OUTCOMES:
        r = est(df, y, ["post3_high"] + CONTROLS)
        out[y] = pack(r, "post3_high")
    return out


def continuous_baseline(df):
    out = {}
    for y in OUTCOMES:
        r = est(df, y, ["post3_x_tddi"] + CONTROLS)
        out[y] = pack(r, "post3_x_tddi")
    return out


def event_study(df, treat="high_tddi", y="log_q", lo=-8, hi=10):
    d = df.copy()
    cols = []
    for k in range(lo, hi + 1):
        if k == -1:
            continue
        c = f"ev_{k}"
        d[c] = ((d["event_time"] == k).astype(float)) * d[treat]
        cols.append(c)
    r = est(d, y, cols + CONTROLS)
    if r is None:
        return None
    rows = []
    for c in cols:
        rows.append({"k": int(c.replace("ev_", "")),
                     "b": float(r.params[c]), "se": float(r.std_errors[c]),
                     "p": float(r.pvalues[c])})
    leads = [c for c in cols if int(c.replace("ev_", "")) < -1]
    b = r.params[leads].to_numpy()
    V = r.cov.loc[leads, leads].to_numpy()
    p_joint = float(chi2.sf(float(b @ np.linalg.pinv(V) @ b), len(leads)))
    return {"rows": rows, "p_joint_leads": p_joint, "n": int(r.nobs)}


def dose_bins(df):
    d = df.copy()
    d["bin"] = pd.qcut(d["tddi"], 5, labels=False, duplicates="drop")
    xs = []
    for b in range(1, int(d["bin"].max()) + 1):
        c = f"post3_bin{b}"
        d[c] = ((d["post3"] == 1) & (d["bin"] == b)).astype(float)
        xs.append(c)
    r = est(d, "log_q", xs + CONTROLS)
    rows = []
    if r is not None:
        for c in xs:
            rows.append({"bin": int(c.replace("post3_bin", "")),
                         "b": float(r.params[c]), "se": float(r.std_errors[c]),
                         "p": float(r.pvalues[c])})
    adj = []
    for b in range(1, int(d["bin"].max()) + 1):
        sub = d[d["bin"].isin([b - 1, b])].copy()
        sub["high"] = (sub["bin"] == b).astype(float)
        sub["post_high"] = sub["post3"] * sub["high"]
        rr = est(sub, "log_q", ["post_high"] + CONTROLS)
        if rr is not None:
            adj.append({"bin": b, "b": float(rr.params["post_high"]),
                        "se": float(rr.std_errors["post_high"]),
                        "p": float(rr.pvalues["post_high"])})
    return {"rows": rows, "adjacent": adj}


def heterogeneity(df):
    out = {}
    for g in ["consumer", "app_high", "fpdci_high"]:
        for val in [0, 1]:
            sub = df[df[g] == val]
            for y in ["log_q", "tobins_q", "gross_margin"]:
                r = est(sub, y, ["post3_high"] + CONTROLS)
                out[f"{g}_{val}_{y}"] = pack(r, "post3_high")
    # top vs bottom tercile
    q1, q2 = df["tddi"].quantile([1 / 3, 2 / 3])
    sub = df[(df["tddi"] <= q1) | (df["tddi"] >= q2)].copy()
    sub["top"] = (sub["tddi"] >= q2).astype(float)
    sub["post_top"] = sub["post3"] * sub["top"]
    for y in ["log_q", "tobins_q", "gross_margin"]:
        r = est(sub, y, ["post_top"] + CONTROLS)
        out[f"top_bottom_{y}"] = pack(r, "post_top")
    return out


def placebo(df):
    out = {}
    for fake in ["2019-09-30", "2020-09-30"]:
        d = df[df["date"] < "2021-06-30"].copy()
        d["fake_post"] = (d["date"] >= pd.Timestamp(fake)).astype(float)
        d["fake_x"] = d["fake_post"] * d["high_tddi"]
        r = est(d, "log_q", ["fake_x"] + CONTROLS)
        out[fake] = pack(r, "fake_x")
    return out


def pipl(df):
    out = {}
    r = est(df, "log_q", ["post3_high", "pipl_high"] + CONTROLS)
    out["att"] = pack(r, "post3_high")
    out["pipl"] = pack(r, "pipl_high")
    return out


def robustness(df):
    out = {}
    # narrow measure (binary)
    r = est(df, "log_q", ["post3_high_narrow"] + CONTROLS)
    out["narrow_binary"] = pack(r, "post3_high_narrow")
    # generic digitalisation placebo
    r = est(df, "log_q", ["post3_x_generic"] + CONTROLS)
    out["generic_placebo"] = pack(r, "post3_x_generic")
    # horse race: high TDDI and generic digitalisation
    d = df.copy()
    d["post3_high_generic"] = d["post3"] * d["high_tddi"] * d["generic_digital"]
    r = est(d, "log_q", ["post3_high", "post3_high_generic"] + CONTROLS)
    out["horse_high"] = pack(r, "post3_high")
    out["horse_generic"] = pack(r, "post3_high_generic")
    # drop COVID year
    d = df[~df["date"].dt.year.eq(2020)]
    r = est(d, "log_q", ["post3_high"] + CONTROLS)
    out["drop_2020"] = pack(r, "post3_high")
    # balanced panel
    cnt = df.groupby("firm_id")["date"].nunique()
    d = df[df["firm_id"].isin(cnt[cnt >= 20].index)]
    r = est(d, "log_q", ["post3_high"] + CONTROLS)
    out["balanced20"] = pack(r, "post3_high")
    # drop largest 1% assets
    d = df[df["assets"] < df["assets"].quantile(0.99)]
    r = est(d, "log_q", ["post3_high"] + CONTROLS)
    out["drop_top1"] = pack(r, "post3_high")
    # COVID interaction
    d = df.copy()
    d["covid"] = ((d["date"] >= "2020-06-30") & (d["date"] <= "2021-06-30")).astype(float)
    d["covid_high"] = d["covid"] * d["high_tddi"]
    r = est(d, "log_q", ["post3_high", "covid_high"] + CONTROLS)
    out["covid_control"] = pack(r, "post3_high")
    out["covid_interaction"] = pack(r, "covid_high")
    # two-way clustered SE
    r = est(df, "log_q", ["post3_high"] + CONTROLS, cluster_time=True)
    out["twoway_cluster"] = pack(r, "post3_high")
    # winsorise 5%
    d = df.copy()
    for c in ["log_q", "tobins_q", "gross_margin"]:
        lo, hi = d[c].quantile([0.05, 0.95])
        d[c] = d[c].clip(lo, hi)
    r = est(d, "log_q", ["post3_high"] + CONTROLS)
    out["winsor5"] = pack(r, "post3_high")
    return out


def wild_bootstrap(df, y="log_q", x="post3_high", reps=999, seed=20260610):
    d = df.dropna(subset=[y, x] + CONTROLS).copy()
    Z = pd.concat([
        pd.get_dummies(d["firm_id"], prefix="f", drop_first=True, dtype=float),
        pd.get_dummies(d["ind_q"], prefix="q", drop_first=True, dtype=float),
    ], axis=1)
    Z = pd.concat([pd.Series(1.0, index=d.index, name="const"),
                   d[CONTROLS].astype(float), Z], axis=1).to_numpy()
    yy = d[y].to_numpy(float)
    xx = d[x].to_numpy(float)
    by = np.linalg.lstsq(Z, yy, rcond=None)[0]
    bx = np.linalg.lstsq(Z, xx, rcond=None)[0]
    ry = yy - Z @ by
    rx = xx - Z @ bx
    b = float(rx @ ry / (rx @ rx))
    clusters = d["firm_id"].to_numpy()
    uniq = np.unique(clusters)
    idx = {c: np.where(clusters == c)[0] for c in uniq}
    rng = np.random.default_rng(seed)
    bs = []
    for _ in range(reps):
        w = rng.choice([-1.0, 1.0], size=len(uniq))
        wy = np.empty_like(ry)
        for c, wc in zip(uniq, w):
            wy[idx[c]] = ry[idx[c]] * wc
        bs.append(float(rx @ wy / (rx @ rx)))
    bs = np.array(bs)
    return {"b": b, "p_wild": float(np.mean(np.abs(bs) >= abs(b))),
            "reps": reps, "q025": float(np.quantile(bs, 0.025)),
            "q975": float(np.quantile(bs, 0.975))}


def main():
    df = load_panel()
    print("panel", df.shape, "firms", df["firm_id"].nunique(),
          "high", df.groupby("firm_id")["high_tddi"].first().mean())
    results = {
        "binary": binary_baseline(df),
        "continuous": continuous_baseline(df),
        "event_binary": event_study(df, "high_tddi"),
        "event_continuous": event_study(df, "tddi"),
        "dose": dose_bins(df),
        "heterogeneity": heterogeneity(df),
        "placebo": placebo(df),
        "pipl": pipl(df),
        "robustness": robustness(df),
        "wild_binary": wild_bootstrap(df),
        "wild_continuous": wild_bootstrap(df, x="post3_x_tddi"),
    }
    with open(os.path.join(OUT, "results_main.json"), "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    def show(d, label):
        print("\n---", label, "---")
        for k, v in d.items():
            if isinstance(v, dict) and v.get("b") is not None:
                print(f"{k:22s} {v['b']: .4f}{v['stars']:3s} se={v['se']:.4f} p={v['p']:.3f} n={v['n']}")

    show(results["binary"], "binary")
    show(results["continuous"], "continuous")
    show(results["heterogeneity"], "heterogeneity")
    show(results["placebo"], "placebo")
    show(results["pipl"], "pipl")
    show(results["robustness"], "robustness")
    print("\nwild binary", results["wild_binary"])
    print("wild continuous", results["wild_continuous"])
    print("\nevent binary joint p", results["event_binary"]["p_joint_leads"])
    for r in results["event_binary"]["rows"]:
        print(r["k"], round(r["b"], 4), round(r["se"], 4), round(r["p"], 3))
    print("\ndose")
    for r in results["dose"]["rows"]:
        print(r)


if __name__ == "__main__":
    main()

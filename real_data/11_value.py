# -*- coding: utf-8 -*-
"""Translate the valuation coefficient into an implied market-value exposure."""
import os
import json
import numpy as np
import pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "real_outputs")

panel = pd.read_csv(os.path.join(BASE, "real_data", "panel.csv"), dtype={"code": str})
panel["date"] = pd.to_datetime(panel["date"])
res = json.load(open(os.path.join(OUT, "results_main.json"), encoding="utf-8"))
b = res["binary"]["log_q"]["b"]
se = res["binary"]["log_q"]["se"]

pre = panel[panel["date"] == pd.Timestamp("2021-03-31")].copy()
base = pre[pre["high_tddi"] == 1].copy()
base["base_value"] = base["mcap"] + base["liab"]
base["dmv"] = b * base["base_value"]
base["dmv_lo"] = (b - 1.96 * se) * base["base_value"]
base["dmv_hi"] = (b + 1.96 * se) * base["base_value"]

by_ind = base.groupby("INDUSTRY_NAME").agg(
    n=("code", "size"), mcap=("mcap", "sum"), base_value=("base_value", "sum"),
    dmv=("dmv", "sum"), dmv_lo=("dmv_lo", "sum"), dmv_hi=("dmv_hi", "sum"),
).reset_index()
for c in ["mcap", "base_value", "dmv", "dmv_lo", "dmv_hi"]:
    by_ind[c + "_bn"] = by_ind[c] / 1e8
by_ind = by_ind.sort_values("dmv_bn")
by_ind.to_csv(os.path.join(OUT, "value_by_industry.csv"), index=False, encoding="utf-8-sig")

summary = {
    "beta_logq": b, "se": se,
    "n_high_firms": int(len(base)),
    "high_mcap_bn": float(base["mcap"].sum() / 1e8),
    "high_base_value_bn": float(base["base_value"].sum() / 1e8),
    "total_dmv_bn": float(base["dmv"].sum() / 1e8),
    "total_dmv_lo_bn": float(base["dmv_lo"].sum() / 1e8),
    "total_dmv_hi_bn": float(base["dmv_hi"].sum() / 1e8),
    "share_of_high_mcap": float(-base["dmv"].sum() / base["mcap"].sum()),
}
pd.DataFrame([summary]).to_csv(os.path.join(OUT, "value_summary.csv"), index=False, encoding="utf-8-sig")
print(summary)
print(by_ind[["INDUSTRY_NAME", "n", "mcap_bn", "dmv_bn", "dmv_lo_bn", "dmv_hi_bn"]].round(1).to_string(index=False))

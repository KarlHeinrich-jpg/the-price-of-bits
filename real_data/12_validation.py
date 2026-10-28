# -*- coding: utf-8 -*-
"""Validation statistics for the TDDI text measure."""
import os
import re
import numpy as np
import pandas as pd
from scipy.stats import pearsonr, spearmanr

from lexicon import CATEGORIES, ALL_TERMS

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MDADIR = os.path.join(BASE, "real_data", "text", "mda")
OUT = os.path.join(BASE, "real_outputs")

panel = pd.read_csv(os.path.join(BASE, "real_data", "panel.csv"), dtype={"code": str})
tddi = pd.read_csv(os.path.join(BASE, "real_data", "tddi.csv"), dtype={"code": str})
tddi["code"] = tddi["code"].str.zfill(6)
panel["code"] = panel["code"].str.zfill(6)
firm = panel.groupby("code").agg(
    tddi=("tddi", "first"), tddi_narrow=("tddi_narrow", "first"),
    fpdci=("fpdci", "first"), generic=("generic_digital", "first"),
    sales_ratio=("sales_ratio", "mean"), gross_margin=("gross_margin", "mean"),
    roa=("roa", "mean"), size=("size", "mean"), leverage=("leverage", "mean"),
    ind=("INDUSTRY_NAME", "first"), high=("high_tddi", "first"),
).reset_index()
# use 2019 values for external validation
panel["date"] = pd.to_datetime(panel["date"])
p19 = panel[panel["date"].dt.year == 2019]
v19 = p19.groupby("code").agg(
    sales_ratio=("sales_ratio", "mean"), gross_margin=("gross_margin", "mean"),
    roa=("roa", "mean"), size=("size", "mean"), leverage=("leverage", "mean"),
).reset_index()
firm = firm.drop(columns=["sales_ratio", "gross_margin", "roa", "size", "leverage"]).merge(v19, on="code", how="left")

rows = []
for x, y in [("tddi", "sales_ratio"), ("tddi", "gross_margin"), ("tddi", "roa"),
             ("tddi", "size"), ("tddi", "leverage"), ("tddi", "generic"),
             ("tddi_narrow", "sales_ratio"), ("tddi_narrow", "gross_margin"),
             ("tddi_narrow", "generic")]:
    d = firm[[x, y]].dropna()
    r, p = pearsonr(d[x], d[y])
    rho, _ = spearmanr(d[x], d[y])
    rows.append({"x": x, "y": y, "pearson": r, "p": p, "spearman": rho, "n": len(d)})
corr = pd.DataFrame(rows)
corr.to_csv(os.path.join(OUT, "validation_correlations.csv"), index=False, encoding="utf-8-sig")
print(corr.round(3).to_string(index=False))

ind = firm.groupby("ind")["tddi"].agg(["mean", "std", "count"]).sort_values("mean", ascending=False)
ind.to_csv(os.path.join(OUT, "tddi_by_industry.csv"), encoding="utf-8-sig")
print("\nTDDI by industry\n", ind.round(2).to_string())

# split-half reliability over the four treatment categories
texts = {}
for fn in os.listdir(MDADIR):
    if fn.endswith(".txt"):
        texts[fn[:-4]] = open(os.path.join(MDADIR, fn), encoding="utf-8").read()
codes = [c for c in firm["code"] if c in texts]
rng = np.random.default_rng(20260610)
terms = [t for t, c in ALL_TERMS if c in
         ["A_data_acquisition", "B_ad_traffic", "C_tracking_targeting", "D_platform_ecosystem"]]
rhos = []
for _ in range(200):
    rng.shuffle(terms)
    h1, h2 = terms[: len(terms) // 2], terms[len(terms) // 2:]
    s1, s2 = [], []
    for c in codes:
        t = texts[c]
        ch = max(len(t), 1) / 10000
        s1.append(sum(t.count(x) for x in h1) / ch)
        s2.append(sum(t.count(x) for x in h2) / ch)
    rhos.append(pearsonr(s1, s2)[0])
r = float(np.mean(rhos))
print(f"\nsplit-half r={r:.3f}, Spearman-Brown={2*r/(1+r):.3f}, n={len(codes)}")
pd.DataFrame({"split_half_r": [r], "spearman_brown": [2*r/(1+r)], "n": [len(codes)]}).to_csv(
    os.path.join(OUT, "tddi_reliability.csv"), index=False, encoding="utf-8-sig")

# -*- coding: utf-8 -*-
"""Construct the Third-party Data Dependency Index from 2019 annual-report MD&A."""
import os
import re
import numpy as np
import pandas as pd

from lexicon import CATEGORIES, ALL_TERMS

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MDADIR = os.path.join(BASE, "real_data", "text", "mda")
OUT = os.path.join(BASE, "real_data", "tddi.csv")

CATS = ["A_data_acquisition", "B_ad_traffic", "C_tracking_targeting",
        "D_platform_ecosystem", "E_first_party", "F_generic_digital"]

# Longest-match alternation: each character span is counted at most once.
TERMS = [t for t, _ in ALL_TERMS] + ["IOS", "App", "app"]
TERMS = sorted(set(TERMS), key=len, reverse=True)
PATTERN = re.compile("|".join(map(re.escape, TERMS)))
TERM_CAT = {}
for t, c in ALL_TERMS:
    TERM_CAT.setdefault(t, c)
for t in ["IOS", "App", "app"]:
    TERM_CAT.setdefault(t, "D_platform_ecosystem")


def count_terms(text):
    counts = {c: 0 for c in CATS}
    for m in PATTERN.finditer(text):
        term = m.group(0)
        cat = TERM_CAT.get(term)
        if cat is None:
            # case variants of iOS
            cat = "D_platform_ecosystem"
        counts[cat] += 1
    return counts


def zs(s):
    s = pd.to_numeric(s, errors="coerce")
    return (s - s.mean()) / s.std(ddof=0)


def main():
    rows = []
    for fn in sorted(os.listdir(MDADIR)):
        if not fn.endswith(".txt"):
            continue
        code = os.path.splitext(fn)[0]
        text = open(os.path.join(MDADIR, fn), encoding="utf-8").read()
        n = max(len(text), 1)
        cnt = count_terms(text)
        row = {"code": code, "chars": n}
        for c in CATS:
            row[c + "_n"] = cnt[c]
            row[c + "_per10k"] = cnt[c] / (n / 10000)
        rows.append(row)
    df = pd.DataFrame(rows)
    for c in CATS:
        df[c + "_z"] = zs(df[c + "_per10k"])
    # Equal-weight the four constructs, then log-transform to limit the
    # influence of a handful of very high-frequency filers.
    raw = df[[c + "_per10k" for c in CATS[:4]]].mean(axis=1)
    df["tddi_raw"] = raw
    df["tddi"] = zs(np.log1p(raw))
    df["tddi_narrow"] = zs(np.log1p(df["A_data_acquisition_per10k"]))
    df["fpdci"] = zs(np.log1p(df["E_first_party_per10k"]))
    df["generic_digital"] = zs(np.log1p(df["F_generic_digital_per10k"]))

    app_terms = ["APP", "App", "app", "移动端", "客户端", "应用商店", "iOS",
                 "安卓", "Android", "小程序", "手机", "移动互联网", "用户数",
                 "月活", "日活", "DAU", "MAU"]
    app_pat = re.compile("|".join(map(re.escape, sorted(app_terms, key=len, reverse=True))))
    app_counts = []
    for fn in sorted(os.listdir(MDADIR)):
        if not fn.endswith(".txt"):
            continue
        text = open(os.path.join(MDADIR, fn), encoding="utf-8").read()
        app_counts.append(len(app_pat.findall(text)) / (max(len(text), 1) / 10000))
    df["app_per10k"] = app_counts
    df["app_exposure"] = zs(np.log1p(df["app_per10k"]))
    df.to_csv(OUT, index=False, encoding="utf-8-sig")
    print(df[["tddi", "tddi_narrow", "fpdci", "generic_digital"]].describe().to_string())
    print("\nTop 10:")
    print(df.nlargest(10, "tddi")[["code", "tddi", "tddi_narrow", "fpdci"]].to_string(index=False))
    print("\nCorrelations:")
    print(df[["tddi", "tddi_narrow", "fpdci", "generic_digital"]].corr().round(2).to_string())


if __name__ == "__main__":
    main()

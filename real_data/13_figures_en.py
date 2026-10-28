# -*- coding: utf-8 -*-
"""English figures with Times New Roman for the MDPI paper."""
import os
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "real_outputs")
FIG = os.path.join(OUT, "figures_en")
os.makedirs(FIG, exist_ok=True)
plt.rcParams.update({
    "font.family": ["Times New Roman"],
    "font.size": 8,
    "axes.unicode_minus": False,
    "axes.linewidth": 0.7,
    "xtick.major.width": 0.6,
    "ytick.major.width": 0.6,
    "xtick.major.size": 2.5,
    "ytick.major.size": 2.5,
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
    "savefig.bbox": "tight",
    "mathtext.fontset": "stix",
})
MM = 1 / 25.4
W = 160 * MM
IND_EN = {"软件开发": "Software development", "通信服务": "Communication services",
          "广告营销": "Advertising and marketing", "IT服务Ⅱ": "IT services",
          "游戏Ⅱ": "Gaming", "数字媒体": "Digital media", "影视院线": "Film and cinema",
          "电视广播Ⅱ": "Broadcasting", "出版": "Publishing",
          "互联网电商": "Internet e-commerce", "教育": "Education"}
def save(fig, name):
    fig.savefig(os.path.join(FIG, name + ".pdf"))
    fig.savefig(os.path.join(FIG, name + ".png"), dpi=400)
    plt.close(fig)
    print("saved", name)
def fig_tddi_industry():
    df = pd.read_csv(os.path.join(OUT, "tddi_by_industry.csv"))
    df["ind_en"] = df["ind"].map(IND_EN)
    df = df.sort_values("mean")
    fig, ax = plt.subplots(figsize=(W, 72 * MM))
    y = np.arange(len(df))
    ax.barh(y, df["mean"], xerr=df["std"] / np.sqrt(df["count"]),
            color="#D9E2F3", edgecolor="black", linewidth=0.7,
            error_kw=dict(ecolor="0.35", lw=0.6, capsize=1.8))
    ax.set_yticks(y)
    ax.set_yticklabels(df["ind_en"])
    ax.axvline(0, color="black", lw=0.6, ls=(0, (3, 2)))
    ax.set_xlabel("TDDI mean (standard deviation units)")
    ax.set_title("Third-party data dependence by industry", fontsize=9)
    for s in ["top", "right"]:
        ax.spines[s].set_visible(False)
    save(fig, "fig2_tddi_industry")
def fig_event():
    res = json.load(open(os.path.join(OUT, "results_main.json"), encoding="utf-8"))
    rows = res["event_binary"]["rows"]
    k = np.array([r["k"] for r in rows])
    b = np.array([r["b"] for r in rows])
    se = np.array([r["se"] for r in rows])
    idx = np.searchsorted(k, -1)
    k = np.insert(k, idx, -1)
    b = np.insert(b, idx, 0.0)
    se = np.insert(se, idx, 0.0)
    fig, ax = plt.subplots(figsize=(W, 78 * MM))
    ax.axvspan(0.5, k.max() + 0.5, color="0.94", lw=0)
    ax.axhline(0, color="black", lw=0.6)
    ax.axvline(0, color="0.3", lw=0.6, ls=(0, (3, 2)))
    ax.axvline(2, color="0.3", lw=0.6, ls=(0, (1, 1.6)))
    ax.errorbar(k, b, yerr=1.96 * se, fmt="o", color="black", ecolor="0.35",
                elinewidth=0.6, capsize=1.6, markersize=3.2)
    ax.plot([-1], [0], "o", mfc="white", mec="black", ms=3.2)
    ax.set_xlabel("Event time relative to 2021Q2 (quarters)")
    ax.set_ylabel("High TDDI × event-time coefficient")
    ax.set_title("Dynamic event study: log Tobin's Q", fontsize=9)
    ax.text(-0.15, 0.155, "ATT effective", fontsize=7, color="0.25", ha="right")
    ax.text(2.15, 0.155, "PIPL effective", fontsize=7, color="0.25", ha="left")
    ax.set_ylim(-0.23, 0.195)
    ax.set_xticks(range(-8, 11, 2))
    for s in ["top", "right"]:
        ax.spines[s].set_visible(False)
    ax.set_xlim(k.min() - 0.5, k.max() + 0.5)
    save(fig, "fig3_event_study")
def fig_dose():
    res = json.load(open(os.path.join(OUT, "results_main.json"), encoding="utf-8"))
    rows = res["dose"]["rows"]
    b = [0.0] + [r["b"] for r in rows]
    se = [0.0] + [r["se"] for r in rows]
    fig, ax = plt.subplots(figsize=(W * 0.7, 72 * MM))
    ax.axhline(0, color="black", lw=0.6)
    ax.errorbar(range(1, 6), b, yerr=1.96 * np.array(se), fmt="o-",
                color="black", ecolor="0.35", elinewidth=0.6, capsize=1.6,
                markersize=3.2, lw=0.8)
    ax.set_xticks(range(1, 6))
    ax.set_xticklabels(["Q1", "Q2", "Q3", "Q4", "Q5"])
    ax.set_xlabel("TDDI quintile")
    ax.set_ylabel("Coefficient relative to Q1")
    ax.set_title("Dose-response: quintile DiD", fontsize=9)
    for s in ["top", "right"]:
        ax.spines[s].set_visible(False)
    save(fig, "fig4_dose_response")
def fig_value():
    df = pd.read_csv(os.path.join(OUT, "value_by_industry.csv"))
    df["ind_en"] = df["INDUSTRY_NAME"].map(IND_EN)
    df = df.sort_values("dmv_bn")
    fig, ax = plt.subplots(figsize=(W * 0.82, 72 * MM))
    y = np.arange(len(df))
    ax.barh(y, -df["dmv_bn"] / 10, color="#F4CCCC", edgecolor="black", linewidth=0.7)
    ax.set_yticks(y)
    ax.set_yticklabels(df["ind_en"])
    ax.set_xlabel("Implied market-value loss (RMB billion)")
    ax.set_title("Data risk exposure by industry", fontsize=9)
    for s in ["top", "right"]:
        ax.spines[s].set_visible(False)
    save(fig, "fig5_value_by_industry")
def fig_timeline():
    fig, ax = plt.subplots(figsize=(W, 42 * MM))
    ax.axhline(0, color="black", lw=0.8, xmin=0.03, xmax=0.97)
    events = [("2020-06", "ATT announced", -1), ("2021-04", "ATT effective", 1),
              ("2021-08", "PIPL adopted", -1), ("2021-11", "PIPL effective", 1)]
    xs = [0.08, 0.36, 0.64, 0.92]
    for (date, label, side), x in zip(events, xs):
        ax.plot([x, x], [-0.08, 0.08], color="black", lw=0.8)
        ax.plot(x, 0, "o", color="black", ms=3.2)
        ax.text(x, 0.16 if side > 0 else -0.22, date, ha="center",
                va="bottom" if side > 0 else "top", fontsize=7.5)
        ax.text(x, 0.32 if side > 0 else -0.38, label, ha="center",
                va="bottom" if side > 0 else "top", fontsize=8)
    ax.set_ylim(-0.55, 0.55)
    ax.axis("off")
    save(fig, "fig1_timeline")
def fig_framework():
    fig, ax = plt.subplots(figsize=(180 * MM, 150 * MM))
    ax.set_xlim(0, 180)
    ax.set_ylim(0, 150)
    ax.axis("off")
    def box(x, y, w, h, title, body, fill):
        p = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.3,rounding_size=1.4",
                           linewidth=0.8, edgecolor="black", facecolor=fill)
        ax.add_patch(p)
        ax.text(x + w / 2, y + h - 3.2, title, ha="center", va="top",
                fontsize=8.6, fontweight="bold")
        ax.text(x + w / 2, y + h / 2 - 2.2, body, ha="center", va="center",
                fontsize=7.6, linespacing=1.35)
    def band(y, label, color):
        ax.text(6, y + 13, label, rotation=90, ha="center", va="center",
                fontsize=8.8, fontweight="bold")
        ax.add_patch(FancyBboxPatch((13, y), 161, 27, boxstyle="round,pad=0.2,rounding_size=1.5",
                                    linewidth=0.6, edgecolor="0.55", facecolor=color))
    band(116, "1. Data", "#EEF4FB")
    box(17, 120, 48, 18, "Sample", "298 A-share digital firms\n11 data-intensive industries", "white")
    box(69, 120, 48, 18, "Panel", "2018Q1–2023Q4\n6,900 firm-quarter observations", "white")
    box(121, 120, 48, 18, "Text", "2019 annual reports\n55,500 characters on average", "white")
    band(83, "2. Measurement", "#EDF7ED")
    box(17, 87, 48, 18, "TDDI", "third-party data acquisition,\ntraffic/ads, tracking, platforms", "white")
    box(69, 87, 48, 18, "FPDCI", "first-party data capability:\naccounts, CRM, private domain", "white")
    box(121, 87, 48, 18, "Placebo", "generic digitalization index\n(dictionary F)", "white")
    band(50, "3. Identification", "#FFF4E6")
    box(17, 54, 48, 18, "Shock", "ATT (April 2021)\n+ PIPL (November 2021)", "white")
    box(69, 54, 48, 18, "Design", "DiD with firm and\nindustry × quarter FE", "white")
    box(121, 54, 48, 18, "Tests", "event study, dose bins,\nplacebo, wild bootstrap", "white")
    band(17, "4. Results", "#F2F2F2")
    box(17, 21, 38, 18, "Valuation", "log Tobin's Q:\n−9.2%", "white")
    box(59, 21, 38, 18, "Margin", "gross margin:\n−2.45 pp", "white")
    box(101, 21, 38, 18, "Heterogeneity", "B2B: −14.2%\nConsumer: n.s.", "white")
    box(143, 21, 29, 18, "Exposure", "RMB 203.7 bn\n(CI 54.7–352.8)", "white")
    for y0, y1 in [(116, 113), (83, 80), (50, 47)]:
        ax.add_patch(FancyArrowPatch((93.5, y0 - 0.5), (93.5, y1 + 0.5),
                                     arrowstyle="-|>", mutation_scale=9,
                                     linewidth=0.8, color="black"))
    save(fig, "fig0_framework")
if __name__ == "__main__":
    fig_tddi_industry()
    fig_event()
    fig_dose()
    fig_value()
    fig_timeline()
    fig_framework()

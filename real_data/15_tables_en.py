# -*- coding: utf-8 -*-
"""Generate English MDPI-style LaTeX tables."""
import os
import json
import pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "real_outputs")
TAB = os.path.join(BASE, "paper_mdpi", "tables")
os.makedirs(TAB, exist_ok=True)

panel = pd.read_csv(os.path.join(BASE, "real_data", "panel.csv"), dtype={"code": str})
panel["date"] = pd.to_datetime(panel["date"])
res = json.load(open(os.path.join(OUT, "results_main.json"), encoding="utf-8"))
val = pd.read_csv(os.path.join(OUT, "validation_correlations.csv"))
rel = pd.read_csv(os.path.join(OUT, "tddi_reliability.csv"))
vind = pd.read_csv(os.path.join(OUT, "value_by_industry.csv"))
vsum = pd.read_csv(os.path.join(OUT, "value_summary.csv"))


def fmt(x, d=4):
    return f"{x:.{d}f}"


def cell(rec, d=4):
    return "--" if rec is None else f"{rec['b']:.{d}f}{rec['stars']}"


def se(rec, d=4):
    return "" if rec is None else f"({rec['se']:.{d}f})"


def write(name, text):
    open(os.path.join(TAB, name), "w", encoding="utf-8").write(text)


# Table 1
pre = panel[panel["date"] < "2021-09-30"]
post = panel[panel["date"] >= "2021-09-30"]
desc_vars = [("log_q", "Log Tobin's Q"), ("tobins_q", "Tobin's Q"),
             ("roa", "ROA"), ("gross_margin", "Gross margin"),
             ("sales_ratio", "Selling-expense ratio"), ("period_ratio", "Period-expense ratio"),
             ("rev_growth", "Revenue growth"), ("size", "Firm size"),
             ("leverage", "Leverage"), ("cash_ratio", "Cash ratio"),
             ("tddi", "TDDI"), ("fpdci", "FPDCI")]
rows = []
for v, lab in desc_vars:
    rows.append(f"{lab} & {panel[v].mean():.3f} & {panel[v].std():.3f} & "
                f"{pre[v].mean():.3f} & {post[v].mean():.3f} \\\\")
desc = "\n".join(rows)
t1 = r"""\begin{table}[htbp]
\centering
\small
\caption{Sample construction and descriptive statistics.}
\label{tab:desc}
\begin{threeparttable}
\begin{tabular}{lcccc}
\toprule
 & Full sample & SD & Pre-shock & Post-shock \\
\midrule
\multicolumn{5}{l}{Panel A: Sample construction} \\
Firms in the 11 digital industries (2021Q1) & 384 & & & \\
\quad Less: no usable 2019 annual report & 86 & & & \\
\quad Final sample & 298 & & & \\
Firm-quarter observations & 6{,}900 & & """ + f"{len(pre):,}" + r""" & """ + f"{len(post):,}" + r""" \\
High-TDDI firms & 100 & & & \\
\midrule
\multicolumn{5}{l}{Panel B: Main variables} \\
""" + desc + r"""
\bottomrule
\end{tabular}
\begin{tablenotes}[flushleft]
\footnotesize
\item Notes: All ratio variables are winsorized at the 1st and 99th percentiles. Pre-shock is 2018Q1--2021Q2; post-shock is 2021Q3--2023Q4. TDDI and FPDCI are standardized to mean zero and unit standard deviation. Firm size is the natural logarithm of total assets.
\end{tablenotes}
\end{threeparttable}
\end{table}
"""
write("table1.tex", t1)

# Table 2
corr_rows = []
for _, r in val.iterrows():
    if r["x"] != "tddi":
        continue
    lab = {"sales_ratio": "Selling-expense ratio", "gross_margin": "Gross margin",
           "roa": "ROA", "size": "Firm size", "leverage": "Leverage",
           "generic": "Generic digitalization"}[r["y"]]
    corr_rows.append(f"{lab} & {r['pearson']:.3f} & {r['spearman']:.3f} & {int(r['n'])} \\\\")
rel_r = float(rel["split_half_r"].iloc[0])
rel_sb = float(rel["spearman_brown"].iloc[0])
t2 = r"""\begin{table}[htbp]
\centering
\small
\caption{Construct validity and reliability of the TDDI.}
\label{tab:validity}
\begin{threeparttable}
\begin{tabular}{lccc}
\toprule
 & Pearson correlation & Spearman correlation & Observations \\
\midrule
\multicolumn{4}{l}{Panel A: Correlations with external proxies and a placebo} \\
""" + "\n".join(corr_rows) + r"""
\midrule
\multicolumn{4}{l}{Panel B: Reliability} \\
Split-half correlation (mean of 200 random splits) & """ + f"{rel_r:.3f}" + r""" & & 298 \\
Spearman--Brown corrected correlation & """ + f"{rel_sb:.3f}" + r""" & & 298 \\
\bottomrule
\end{tabular}
\begin{tablenotes}[flushleft]
\footnotesize
\item Notes: External proxies are 2019 firm-level averages. The TDDI is constructed from 2019 annual-report texts. The generic digitalization index is the standardized frequency of category F terms and serves as a placebo. The split-half correlation randomly divides the A--D terms into two halves and correlates the resulting indices across firms.
\end{tablenotes}
\end{threeparttable}
\end{table}
"""
write("table2.tex", t2)

# Table 3
base_vars = ["log_q", "tobins_q", "gross_margin", "roa", "sales_ratio"]
short = {"log_q": "Log Tobin's Q", "tobins_q": "Tobin's Q", "gross_margin": "Gross margin",
         "roa": "ROA", "sales_ratio": "Selling-expense ratio"}
headers = " & ".join([f"({i+1}) {short[v]}" for i, v in enumerate(base_vars)])
row_b = " & ".join([cell(res["binary"][v]) for v in base_vars])
row_b_se = " & ".join([se(res["binary"][v]) for v in base_vars])
row_c = " & ".join([cell(res["continuous"][v]) for v in base_vars])
row_c_se = " & ".join([se(res["continuous"][v]) for v in base_vars])
ns = " & ".join([f"{res['binary'][v]['n']:,}" for v in base_vars])
r2s = " & ".join([f"{res['binary'][v]['r2']:.3f}" for v in base_vars])
t3 = r"""\begin{table}[htbp]
\centering
\small
\setlength{\tabcolsep}{4pt}
\caption{Baseline difference-in-differences estimates.}
\label{tab:main}
\begin{threeparttable}
\begin{tabular}{lccccc}
\toprule
""" + headers + r""" \\
\midrule
\multicolumn{6}{l}{Panel A: High-TDDI firms (top third)} \\
High TDDI $\times$ Post & """ + row_b + r""" \\
 & """ + row_b_se + r""" \\
\midrule
\multicolumn{6}{l}{Panel B: Continuous TDDI (one-standard-deviation increase)} \\
TDDI $\times$ Post & """ + row_c + r""" \\
 & """ + row_c_se + r""" \\
\midrule
Controls & Yes & Yes & Yes & Yes & Yes \\
Firm FE & Yes & Yes & Yes & Yes & Yes \\
Industry $\times$ Quarter FE & Yes & Yes & Yes & Yes & Yes \\
Observations & """ + ns + r""" \\
$R^2$ & """ + r2s + r""" \\
\bottomrule
\end{tabular}
\begin{tablenotes}[flushleft]
\footnotesize
\item Notes: Standard errors clustered by firm are in parentheses. ***, **, and * denote significance at the 1\%, 5\%, and 10\% levels. Post equals one for 2021Q3 and later. High TDDI indicates the top third of the TDDI distribution; the comparison group is the rest of the sample. Controls include lagged firm size, leverage, and the cash ratio. The TDDI is standardized in Panel B.
\end{tablenotes}
\end{threeparttable}
\end{table}
"""
write("table3.tex", t3)

# Table 4
groups = [("consumer_0", "B2B firms"), ("consumer_1", "Consumer firms"),
          ("app_high_0", "Low app exposure"), ("app_high_1", "High app exposure"),
          ("fpdci_high_0", "Low FPDCI"), ("fpdci_high_1", "High FPDCI")]
rows = []
for key, lab in groups:
    cells = []
    for y in ["log_q", "tobins_q", "gross_margin"]:
        rec = res["heterogeneity"].get(f"{key}_{y}")
        cells.append(f"{cell(rec)} {se(rec)}" if rec else "--")
    rows.append(f"{lab} & " + " & ".join(cells) + r" \\")
t4 = r"""\begin{table}[htbp]
\centering
\small
\caption{Heterogeneity by firm type, app exposure, and first-party data capability.}
\label{tab:hetero}
\begin{threeparttable}
\begin{tabular}{lccc}
\toprule
 & Log Tobin's Q & Tobin's Q & Gross margin \\
\midrule
""" + "\n".join(rows) + r"""
\bottomrule
\end{tabular}
\begin{tablenotes}[flushleft]
\footnotesize
\item Notes: Each cell reports the coefficient on High TDDI $\times$ Post, with firm-clustered standard errors in parentheses. B2B firms include IT services, software development, and communication services. Consumer firms include advertising, gaming, e-commerce, digital media, film, publishing, broadcasting, and education. App exposure and FPDCI are split at the median. The top-third versus bottom-third comparison is reported in the text.
\end{tablenotes}
\end{threeparttable}
\end{table}
"""
write("table4.tex", t4)

# Table 5
rb = res["robustness"]
rows = [
    ("Baseline: high TDDI", res["binary"]["log_q"]),
    ("Narrow TDDI measure", rb["narrow_binary"]),
    ("Placebo: generic digitalization", rb["generic_placebo"]),
    ("Horse race: TDDI and generic digitalization", rb["horse_high"]),
    ("Excluding 2020", rb["drop_2020"]),
    ("Balanced panel (at least 20 quarters)", rb["balanced20"]),
    ("Excluding the top 1\\% by assets", rb["drop_top1"]),
    ("Controlling for the 2020--2021 pandemic interaction", rb["covid_control"]),
    ("Two-way clustering (firm and quarter)", rb["twoway_cluster"]),
    ("Winsorizing at the 5th and 95th percentiles", rb["winsor5"]),
    ("Top third versus bottom third", res["heterogeneity"]["top_bottom_log_q"]),
]
rows_txt = []
for lab, rec in rows:
    rows_txt.append(f"{lab} & {cell(rec)} & {se(rec)} & {rec['p']:.3f} & {rec['n']:,} \\\\")
t5 = r"""\begin{table}[htbp]
\centering
\small
\caption{Robustness checks for log Tobin's Q.}
\label{tab:robust}
\begin{threeparttable}
\begin{tabular}{lcccc}
\toprule
 & Coefficient & Standard error & $p$-value & Observations \\
\midrule
""" + "\n".join(rows_txt) + r"""
\bottomrule
\end{tabular}
\begin{tablenotes}[flushleft]
\footnotesize
\item Notes: All columns use log Tobin's Q as the dependent variable and include firm fixed effects, industry-by-quarter fixed effects, and controls. The wild cluster bootstrap $p$-value for the baseline coefficient is 0.007 (999 replications). The generic digitalization index is the standardized frequency of category F terms; it should be insignificant if the TDDI captures a distinct construct.
\end{tablenotes}
\end{threeparttable}
\end{table}
"""
write("table5.tex", t5)

# Table 6
v = vind.sort_values("dmv_bn")
IND_EN = {"软件开发": "Software development", "通信服务": "Communication services",
          "广告营销": "Advertising and marketing", "IT服务Ⅱ": "IT services",
          "游戏Ⅱ": "Gaming", "数字媒体": "Digital media", "影视院线": "Film and cinema",
          "电视广播Ⅱ": "Broadcasting", "出版": "Publishing",
          "互联网电商": "Internet e-commerce", "教育": "Education"}
rows = []
for _, r in v.iterrows():
    ind = IND_EN.get(r["INDUSTRY_NAME"], r["INDUSTRY_NAME"])
    rows.append(f"{ind} & {int(r['n'])} & {r['mcap_bn']/10:.1f} & "
                f"{-r['dmv_bn']/10:.1f} & {-r['dmv_hi_bn']/10:.1f} & {-r['dmv_lo_bn']/10:.1f} \\\\")
total = vsum.iloc[0]
rows.append(r"\midrule")
rows.append(f"Total & {int(total['n_high_firms'])} & {total['high_mcap_bn']/10:.1f} & "
            f"{-total['total_dmv_bn']/10:.1f} & {-total['total_dmv_hi_bn']/10:.1f} & "
            f"{-total['total_dmv_lo_bn']/10:.1f} \\\\")
t6 = r"""\begin{table}[htbp]
\centering
\small
\small
\setlength{\tabcolsep}{3pt}
\caption{Implied market-value loss of high-TDDI firms by industry.}
\label{tab:value}
\begin{threeparttable}
\begin{tabular}{lccccc}
\toprule
Industry & Firms & Market value (RMB bn) & Implied loss (RMB bn) & 95\% lower & 95\% upper \\
\midrule
""" + "\n".join(rows) + r"""
\bottomrule
\end{tabular}
\begin{tablenotes}[flushleft]
\footnotesize
\item Notes: The implied loss applies the baseline log Tobin's Q coefficient ($-0.0917$) to the sum of 2021Q1 equity market value and liabilities. Confidence intervals use the coefficient standard error times $\pm1.96$. The sample contains the 100 high-TDDI firms. The estimate is the market-value exposure to the privacy shock, not the total value of all data assets.
\end{tablenotes}
\end{threeparttable}
\end{table}
"""
write("table6.tex", t6)

# Table A1
vd = r"""\begin{table}[htbp]
\centering
\small
\caption{Variable definitions and data sources.}
\label{tab:vars}
\begin{threeparttable}
\begin{tabular}{p{3.2cm}p{8.4cm}p{3.2cm}}
\toprule
Variable & Definition & Source \\
\midrule
TDDI & Equal-weighted average of the A--D term frequencies, log-transformed and standardized & 2019 annual reports; authors' construction \\
FPDCI & Log-standardized frequency of first-party data terms & 2019 annual reports; authors' construction \\
Tobin's Q & (Equity market value + total liabilities) / total assets & Eastmoney \\
Log Tobin's Q & Natural logarithm of Tobin's Q & Authors' calculation \\
ROA & Net profit attributable to the parent / total assets & Eastmoney \\
Gross margin & (Operating revenue $-$ operating costs) / operating revenue & Eastmoney \\
Selling-expense ratio & Selling expenses / operating revenue & Eastmoney \\
Period-expense ratio & (Selling + administrative expenses) / operating revenue & Eastmoney \\
Firm size & Natural logarithm of total assets & Authors' calculation \\
Leverage & Total liabilities / total assets & Authors' calculation \\
Cash ratio & Cash holdings / total assets & Authors' calculation \\
High TDDI & Top third of the TDDI distribution & Authors' construction \\
Post & 2021Q3 and later & Authors' construction \\
\bottomrule
\end{tabular}
\begin{tablenotes}[flushleft]
\footnotesize
\item Notes: Financial variables are quarterly. Flow variables are differenced from year-to-date cumulative values. Ratio variables are winsorized at the 1st and 99th percentiles.
\end{tablenotes}
\end{threeparttable}
\end{table}
"""
write("tableA1.tex", vd)

# Table A2
lex = r"""\begin{table}[htbp]
\centering
\small
\caption{TDDI lexicon: constructs and representative terms.}
\label{tab:lexicon}
\begin{threeparttable}
\begin{tabular}{p{3.2cm}p{10.0cm}p{1.2cm}}
\toprule
Construct & Representative terms & Terms \\
\midrule
A. Third-party data acquisition & third-party data, purchased data, data procurement, data supplier, data transaction, data sharing, data interface, data source, data fusion & 33 \\
B. Third-party traffic and advertising & traffic purchase, customer acquisition cost, ad buying, advertising placement, precision marketing, programmatic advertising, information-flow advertising, ad network, app distribution & 37 \\
C. User profiling and tracking & user profile, tag system, cross-app, cross-device, device identifier, IDFA, OAID, targeted placement, personalized recommendation, audience package & 30 \\
D. Platform dependence & third-party platform, open platform, app store, iOS, WeChat mini-program, Douyin, Kuaishou, Xiaohongshu, Ocean Engine, Alimama & 26 \\
E. First-party data capability & owned data, first-party data, private-domain traffic, membership system, user community, WeCom, CRM, data middle platform, CDP & 28 \\
F. Generic digitalization (placebo) & digital transformation, cloud computing, big data, artificial intelligence, Internet of Things, blockchain, 5G, industrial internet, large language model & 18 \\
\bottomrule
\end{tabular}
\begin{tablenotes}[flushleft]
\footnotesize
\item Notes: The longest-match rule ensures that each character span is counted once. Frequencies are normalized per 10,000 characters. The complete list is in the replication code.
\end{tablenotes}
\end{threeparttable}
\end{table}
"""
write("tableA2.tex", lex)

# Table A3 event study
rows = []
for r in res["event_binary"]["rows"]:
    rows.append(f"{r['k']} & {r['b']:.4f}{'***' if r['p']<0.01 else '**' if r['p']<0.05 else '*' if r['p']<0.1 else ''} & {r['se']:.4f} \\\\")
t7 = r"""\begin{table}[htbp]
\centering
\small
\caption{Full event-study coefficients for log Tobin's Q.}
\label{tab:event}
\begin{threeparttable}
\begin{tabular}{lcc}
\toprule
Event time $k$ & Coefficient & Standard error \\
\midrule
""" + "\n".join(rows) + r"""
\bottomrule
\end{tabular}
\begin{tablenotes}[flushleft]
\footnotesize
\item Notes: The dependent variable is log Tobin's Q. Event time is measured in quarters relative to 2021Q2; $k=-1$ is the omitted reference period. All regressions include firm fixed effects, industry-by-quarter fixed effects, and controls. The joint test on the leads yields $p=0.079$.
\end{tablenotes}
\end{threeparttable}
\end{table}
"""
write("table7.tex", t7)

print("English tables written to", TAB)

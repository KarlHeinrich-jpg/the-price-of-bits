# The Price of Bits

**Privacy Shocks, Third-Party Data Dependence, and the Valuation of Digital Firms**

This repository contains the paper, the processed real data, the analysis code, and the figures for the project *The Price of Bits*. The empirical setting is the 2021 privacy regime—Apple's App Tracking Transparency (ATT) and China's Personal Information Protection Law (PIPL)—and the sample is 298 Chinese A-share digital firms over 2018Q1–2023Q4.

- **Paper (PDF):** [`paper/main.pdf`](paper/main.pdf)
- **LaTeX source:** [`paper/main.tex`](paper/main.tex)
- **Processed panel:** [`real_data/panel.csv`](real_data/panel.csv)
- **TDDI / FPDCI scores:** [`real_data/tddi.csv`](real_data/tddi.csv)
- **Variable dictionary:** [`real_data/data_dictionary_real.csv`](real_data/data_dictionary_real.csv)
- **Figures:** [`figures/`](figures/)
- **Main results:** [`real_outputs/results_main.json`](real_outputs/results_main.json)

## Abstract

Data are a core production factor of the digital economy, yet their asset value lacks an observable market price. This paper exploits the 2021 Apple App Tracking Transparency (ATT) policy and China's Personal Information Protection Law (PIPL) as a privacy-regime shock. We construct a text-based Third-Party Data Dependency Index (TDDI) from the 2019 annual reports of 298 Chinese A-share digital firms and estimate difference-in-differences models on a firm-quarter panel from 2018Q1 to 2023Q4. Firms in the top third of TDDI experience a 9.2% relative decline in log Tobin's Q and a 2.45 percentage-point decline in gross margin after the shock; ROA and selling-expense ratios do not change significantly. The effect is concentrated in B2B data-service firms, whereas consumer internet firms are not significantly affected. The implied market-value loss for high-exposure firms is RMB 203.7 billion (95% CI: 54.7–352.8 billion).

## Key results

| Outcome | Estimate | Note |
|---|---:|---|
| Log Tobin's Q | −0.0917*** (0.0343) | Top-third TDDI × post-2021Q3 |
| Tobin's Q | −0.3596*** (0.1244) | Level effect |
| Gross margin | −0.0245** (0.0110) | 2.45 percentage points |
| ROA | 0.0004 (0.0023) | Not significant |
| Selling-expense ratio | −0.0093 (0.0077) | Not significant |
| B2B firms | −0.1424*** (0.0438) | Log Tobin's Q |
| Consumer firms | −0.0197 (0.0523) | Not significant |
| Implied market-value loss | RMB 203.7 bn | 95% CI: 54.7–352.8 bn |

The wild cluster bootstrap *p*-value for the baseline coefficient is 0.007 (999 replications). The event study rejects a flat pre-trend at the 10% level (*p* = 0.079); the paper reports placebo, dose-response, and robustness tests.

## Repository structure

```
paper/                  Paper PDF, LaTeX source, sections, tables
figures/                All figures (PDF + PNG), Times New Roman only
real_data/              Processed data, TDDI, raw CSV downloads, analysis scripts
  panel.csv             Firm-quarter panel, 6,900 observations
  tddi.csv              TDDI, FPDCI, generic digitalization index
  data_dictionary_real.csv
  raw/                  Raw financial statements, valuations, Sina financials, prices
  text/extraction_log.csv
  *.py                  Download, text extraction, panel construction, estimation, figures
real_outputs/           Main results, validation, value estimates, event-study outputs
```

## Data sources

- **Financial statements and valuations:** Eastmoney data center (quarterly balance sheets, income statements, quarter-end market capitalization).
- **Cross-checks and daily prices:** Sina Finance.
- **Annual reports:** CNINFO and Eastmoney disclosure platforms. The 2019 annual-report PDFs are **not** included in this repository because of size and copyright; the download and text-extraction scripts are provided.
- **Sample frame:** 11 data-intensive industries in the 2021Q1 Eastmoney industry classification (IT services, software, communication services, advertising, publishing, gaming, education, film, internet e-commerce, digital media, broadcasting).

The TDDI is a dictionary-based text measure (longest-match, length-normalized, log-standardized), not an LLM score. The full lexicon is in `real_data/lexicon.py`; the validation statistics are in `real_outputs/validation_correlations.csv` and `real_outputs/tddi_reliability.csv`.

## Reproduction

```bash
pip install -r real_data/requirements.txt

# 1. Download financial statements and valuations
python real_data/01c_download_statements.py balance
python real_data/01c_download_statements.py income
python real_data/04_download_valuation.py

# 2. Download 2019 annual-report PDFs
python real_data/02_download_reports.py

# 3. Extract MD&A text and construct TDDI
python real_data/06_extract_text.py
cd real_data && python 07_build_tddi.py && cd ..

# 4. Build the panel
cd real_data && python 08_build_panel.py && cd ..

# 5. Main results, validation, value estimate
cd real_data && python 09_main_results.py && python 12_validation.py && python 11_value.py && cd ..

# 6. Figures and tables
cd real_data && python 13_figures_en.py && python 15_tables_en.py && cd ..

# 7. Compile the paper (two passes)
cd paper && pdflatex main.tex && pdflatex main.tex && cd ..
```

The scripts use direct HTTP connections and ignore local proxy settings via `real_data/net.py`. If your environment requires a proxy, remove the `net` import or set the proxy explicitly.

## Data availability and scope

- The processed panel, TDDI scores, validation outputs, results, and all figures are included.
- The raw CSV downloads are included under `real_data/raw/` (about 49 MB).
- The annual-report PDFs and the extracted MD&A texts are not redistributed; they can be re-downloaded from the public disclosure platforms with the provided scripts.
- The estimate is a firm-side market-value exposure to the 2021 privacy regime, not the total value of all data assets or a social-welfare measure.

## Licenses

- **Code:** MIT License (see `LICENSE`).
- **Data and figures:** Creative Commons Attribution 4.0 International (CC BY 4.0; see `DATA_LICENSE`).
- **Paper:** CC BY 4.0.

## Citation

If you use this repository, please cite:

```bibtex
@misc{wang2026priceofbits,
  author = {Wang, Yile},
  title = {The Price of Bits: Privacy Shocks, Third-Party Data Dependence, and the Valuation of Digital Firms},
  year = {2026},
  howpublished = {\url{https://github.com/KarlHeinrich-jpg/the-price-of-bits}}
}
```

## Contact

Yile Wang — email@example.com

The paper is prepared for submission to the *Journal of Theoretical and Applied Electronic Commerce Research* (JTAER, MDPI).

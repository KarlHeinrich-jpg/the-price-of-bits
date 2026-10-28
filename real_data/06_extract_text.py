# -*- coding: utf-8 -*-
"""Extract the MD&A section from each 2019 annual report PDF."""
import os
import re
import pandas as pd
import pymupdf

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PDFDIR = os.path.join(BASE, "real_data", "text", "pdf")
OUTDIR = os.path.join(BASE, "real_data", "text", "mda")
os.makedirs(OUTDIR, exist_ok=True)

START_PATS = ["公司业务概要", "经营情况讨论与分析", "管理层讨论与分析", "董事会报告"]
END_PATS = ["重要事项", "公司治理", "监事会报告", "环境和社会责任", "社会责任", "财务报告"]


def page_text(doc):
    parts = []
    for page in doc:
        t = page.get_text("text")
        lines = []
        for line in t.splitlines():
            s = line.strip()
            if not s:
                continue
            if len(s) < 60 and re.search(r"(年度报告(全文)?|第\s*\d+\s*页|^\d{1,3}$)", s):
                continue
            lines.append(s)
        parts.append("\n".join(lines))
    return "\n".join(parts)


def compact(t):
    t = t.replace("\u3000", " ")
    t = re.sub(r"[ \t\r\f\v]+", "", t)
    t = re.sub(r"\n+", "\n", t)
    return t


def extract_mda(text):
    """Take a fixed 60k-character window from the body MD&A heading.

    Annual-report section boundaries are inconsistent across filers, and
    '重要事项' appears inside the MD&A as a cross-reference.  A fixed window
    from the business-discussion heading is more robust than heading-based
    trimming; keyword counts are normalised by the realised window length.
    """
    best = None
    for sp in START_PATS:
        idxs = [m.start() for m in re.finditer(sp, text)]
        for i in idxs:
            if i < 5000:
                continue
            if best is None or i < best[2]:
                best = (sp, None, i, None)
    if best:
        i = best[2]
        end = min(len(text), i + 60000)
        seg = text[i:end]
        if len(seg) >= 8000:
            return (best[0], seg, i, end)
    return ("fallback", text[8000:80000], 8000, 80000)


def main():
    rows = []
    for fn in sorted(os.listdir(PDFDIR)):
        if not fn.lower().endswith(".pdf"):
            continue
        code = os.path.splitext(fn)[0]
        out = os.path.join(OUTDIR, f"{code}.txt")
        try:
            doc = pymupdf.open(os.path.join(PDFDIR, fn))
            text = compact(page_text(doc))
            heading, seg, i, j = extract_mda(text)
            seg = re.sub(r"\n", "", seg)
            with open(out, "w", encoding="utf-8") as f:
                f.write(seg)
            rows.append({"code": code, "pages": doc.page_count, "chars_full": len(text),
                         "chars_mda": len(seg), "heading": heading})
        except Exception as e:
            rows.append({"code": code, "pages": None, "chars_full": 0,
                         "chars_mda": 0, "heading": f"ERROR:{type(e).__name__}"})
    meta = pd.DataFrame(rows)
    meta.to_csv(os.path.join(BASE, "real_data", "text", "extraction_log.csv"),
                index=False, encoding="utf-8-sig")
    print(meta["heading"].value_counts().to_string())
    print(meta["chars_mda"].describe().to_string())


if __name__ == "__main__":
    main()

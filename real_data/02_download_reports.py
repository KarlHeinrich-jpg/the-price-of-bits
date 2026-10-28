# -*- coding: utf-8 -*-
"""Download 2019 annual reports (published 2020) for the sample firms.

Source: Eastmoney notice API + pdf.dfcfw.com CDN.
"""
import os
import re
import json
import time
import threading
import requests
import pandas as pd
import net
from concurrent.futures import ThreadPoolExecutor, as_completed

for k in list(os.environ):
    if "proxy" in k.lower():
        os.environ.pop(k, None)

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(BASE, "real_data", "raw")
PDFDIR = os.path.join(BASE, "real_data", "text", "pdf")
os.makedirs(PDFDIR, exist_ok=True)

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
           "Referer": "https://data.eastmoney.com/notices/"}
SEARCH = ("https://np-anotice-stock.eastmoney.com/api/security/ann"
          "?sr=-1&page_size=100&page_index={page}&ann_type=A&client_source=web"
          "&stock_list={code}&begin_time={begin}&end_time={end}")
LOCK = threading.Lock()


def get_codes():
    path = os.path.join(BASE, "real_data", "sample_codes.csv")
    df = pd.read_csv(path, dtype={"SECURITY_CODE": str})
    df["SECURITY_CODE"] = df["SECURITY_CODE"].str.zfill(6)
    return df[["SECURITY_CODE", "SECURITY_NAME_ABBR", "INDUSTRY_NAME"]].drop_duplicates("SECURITY_CODE")


def fetch_anns(code, begin, end, max_pages=3):
    anns = []
    for page in range(1, max_pages + 1):
        got = []
        for attempt in range(4):
            try:
                r = requests.get(SEARCH.format(code=code, page=page, begin=begin, end=end),
                                 headers=HEADERS, timeout=40)
                got = (r.json().get("data") or {}).get("list") or []
                break
            except Exception:
                time.sleep(1.5 * (attempt + 1))
        anns += got
        if len(got) < 100:
            break
    return anns


def find_report(code):
    anns = fetch_anns(code, "2020-03-01", "2020-06-30", 1)
    if not any("2019" in (a.get("title") or "") for a in anns):
        anns += fetch_anns(code, "2020-06-01", "2020-12-31", 2)
    if not any("2019" in (a.get("title") or "") for a in anns):
        anns += fetch_anns(code, "2020-01-01", "2020-12-31", 3)
    cand = []
    for a in anns:
        t = a.get("title") or ""
        if "2019" not in t:
            continue
        if not re.search(r"2019年?年度报告", t):
            continue
        if any(x in t for x in ["摘要", "英文", "半年度", "季度", "社会责任",
                                "审计报告", "问询", "回复", "说明", "致辞"]):
            continue
        cand.append(a)
    if not cand:
        return None
    cand.sort(key=lambda a: a.get("notice_date") or "", reverse=True)
    return cand[0]


def download_one(row):
    code = row["SECURITY_CODE"]
    out = os.path.join(PDFDIR, f"{code}.pdf")
    if os.path.exists(out) and os.path.getsize(out) > 300000:
        with open(out, "rb") as fh:
            if fh.read(4) == b"%PDF":
                return {"code": code, "status": "cached", "bytes": os.path.getsize(out)}
        os.remove(out)
    a = find_report(code)
    if a is None:
        return {"code": code, "status": "not_found"}
    art = a.get("art_code")
    title = a.get("title")
    url = f"http://pdf.dfcfw.com/pdf/H2_{art}_1.pdf"
    for attempt in range(5):
        try:
            r = requests.get(url, headers=HEADERS, timeout=120, stream=True)
            if (r.status_code == 200 and len(r.content) > 100000
                    and r.content[:4] == b"%PDF"):
                with open(out, "wb") as f:
                    f.write(r.content)
                return {"code": code, "status": "ok", "bytes": len(r.content),
                        "title": title, "date": str(a.get("notice_date"))[:10]}
            time.sleep(1.0 * (attempt + 1))
        except Exception:
            time.sleep(1.5 * (attempt + 1))
    return {"code": code, "status": "download_failed", "title": title}


def main():
    codes = get_codes()
    codes.to_csv(os.path.join(BASE, "real_data", "sample_codes.csv"), index=False,
                 encoding="utf-8-sig")
    print(f"codes: {len(codes)}", flush=True)
    rows = []
    with ThreadPoolExecutor(max_workers=4) as ex:
        futs = {ex.submit(download_one, row): row for _, row in codes.iterrows()}
        for i, f in enumerate(as_completed(futs), 1):
            try:
                rec = f.result()
            except Exception as e:
                rec = {"code": futs[f]["SECURITY_CODE"], "status": f"error:{type(e).__name__}"}
            rows.append(rec)
            with LOCK:
                print(i, rec.get("code"), rec.get("status"), rec.get("bytes", ""), flush=True)
    meta = pd.DataFrame(rows)
    meta.to_csv(os.path.join(BASE, "real_data", "report_download_log.csv"),
                index=False, encoding="utf-8-sig")
    print(meta["status"].value_counts().to_string(), flush=True)


if __name__ == "__main__":
    main()

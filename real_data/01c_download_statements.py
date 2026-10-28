# -*- coding: utf-8 -*-
"""Download absolute balance-sheet and income-statement items (Eastmoney)."""
import os
import sys
import time
import requests
import pandas as pd
import net
from concurrent.futures import ThreadPoolExecutor, as_completed

for k in list(os.environ):
    if "proxy" in k.lower():
        os.environ.pop(k, None)

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(BASE, "real_data", "raw")
URL = "https://datacenter-web.eastmoney.com/api/data/v1/get"
H = {"User-Agent": "Mozilla/5.0", "Accept-Encoding": "gzip, deflate"}
INDS = ["IT服务Ⅱ", "软件开发", "通信服务", "广告营销", "出版", "游戏Ⅱ",
        "教育", "影视院线", "互联网电商", "数字媒体", "电视广播Ⅱ"]
IND_LIST = ",".join([f'"{x}"' for x in INDS])
DATES = [str(d)[:10] for d in pd.date_range("2017-12-31", "2023-12-31", freq="QE")]

BS_COLS = ("SECUCODE,SECURITY_CODE,SECURITY_NAME_ABBR,INDUSTRY_NAME,REPORT_DATE,"
           "TOTAL_ASSETS,TOTAL_LIABILITIES,TOTAL_EQUITY,MONETARYFUNDS")
IS_COLS = ("SECUCODE,SECURITY_CODE,SECURITY_NAME_ABBR,INDUSTRY_NAME,REPORT_DATE,"
           "TOTAL_OPERATE_INCOME,OPERATE_COST,SALE_EXPENSE,MANAGE_EXPENSE,"
           "OPERATE_PROFIT,PARENT_NETPROFIT")


def fetch(report, cols, flt):
    rows, page, pages = [], 1, 1
    while page <= pages:
        params = {"reportName": report, "columns": cols, "filter": flt,
                  "pageNumber": str(page), "pageSize": "500",
                  "source": "WEB", "client": "WEB"}
        j = None
        for attempt in range(6):
            try:
                r = requests.get(URL, params=params, headers=H, timeout=150)
                j = r.json()
                if j.get("success"):
                    break
            except Exception:
                time.sleep(2.5 * (attempt + 1))
        res = (j or {}).get("result") or {}
        rows += res.get("data") or []
        pages = res.get("pages") or 1
        page += 1
        time.sleep(0.3)
    return rows


def one_balance(ds):
    out = os.path.join(RAW, f"balance_{ds}.csv")
    if os.path.exists(out) and os.path.getsize(out) > 1000:
        return ds, "cached"
    flt = f"(REPORT_DATE='{ds}')(INDUSTRY_NAME in ({IND_LIST}))"
    rows = fetch("RPT_DMSK_FN_BALANCE", BS_COLS, flt)
    if rows:
        pd.DataFrame(rows).to_csv(out, index=False, encoding="utf-8-sig")
    return ds, len(rows)


def one_income(ds, ind):
    out = os.path.join(RAW, f"income_{ds}_{ind}.csv")
    if os.path.exists(out) and os.path.getsize(out) > 500:
        return ds, ind, "cached"
    flt = f"(REPORT_DATE='{ds}')(INDUSTRY_NAME=\"{ind}\")"
    rows = fetch("RPT_DMSK_FN_INCOME", IS_COLS, flt)
    if rows:
        pd.DataFrame(rows).to_csv(out, index=False, encoding="utf-8-sig")
    return ds, ind, len(rows)


def main(which):
    if which == "balance":
        with ThreadPoolExecutor(max_workers=2) as ex:
            for ds, res in ex.map(one_balance, DATES):
                print(ds, res, flush=True)
    elif which == "income":
        jobs = [(ds, ind) for ds in DATES for ind in INDS]
        with ThreadPoolExecutor(max_workers=4) as ex:
            futs = {ex.submit(one_income, ds, ind): (ds, ind) for ds, ind in jobs}
            for i, f in enumerate(as_completed(futs), 1):
                print(i, f.result(), flush=True)
    print("DONE", flush=True)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "balance")

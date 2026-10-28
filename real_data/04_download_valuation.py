# -*- coding: utf-8 -*-
"""Quarter-end market capitalization / PB for the sample boards (Eastmoney)."""
import os
import time
import requests
import pandas as pd
import net

for k in list(os.environ):
    if "proxy" in k.lower():
        os.environ.pop(k, None)

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(BASE, "real_data", "raw")
URL = "https://datacenter-web.eastmoney.com/api/data/v1/get"
HEADERS = {"User-Agent": "Mozilla/5.0", "Accept-Encoding": "gzip, deflate"}
INDS = ["IT服务Ⅱ", "软件开发", "通信服务", "广告营销", "出版", "游戏Ⅱ",
        "教育", "影视院线", "互联网电商", "数字媒体", "电视广播Ⅱ"]
IND_LIST = ",".join([f'"{x}"' for x in INDS])
COLS = ("SECUCODE,SECURITY_CODE,SECURITY_NAME_ABBR,BOARD_NAME,TRADE_DATE,"
        "TOTAL_MARKET_CAP,TOTAL_SHARES,PB_MRQ,CLOSE_PRICE")
DATES = [
    "2017-12-29", "2018-03-30", "2018-06-29", "2018-09-28", "2018-12-28",
    "2019-03-29", "2019-06-28", "2019-09-30", "2019-12-31", "2020-03-31",
    "2020-06-30", "2020-09-30", "2020-12-31", "2021-03-31", "2021-06-30",
    "2021-09-30", "2021-12-31", "2022-03-31", "2022-06-30", "2022-09-30",
    "2022-12-30", "2023-03-31", "2023-06-30", "2023-09-28", "2023-12-29",
]


def fetch(ds):
    rows = []
    page = 1
    pages = 1
    while page <= pages:
        params = {"reportName": "RPT_VALUEANALYSIS_DET", "columns": COLS,
                  "filter": f"(TRADE_DATE='{ds}')(BOARD_NAME in ({IND_LIST}))",
                  "pageNumber": str(page), "pageSize": "500",
                  "source": "WEB", "client": "WEB"}
        j = None
        for attempt in range(6):
            try:
                r = requests.get(URL, params=params, headers=HEADERS, timeout=120)
                j = r.json()
                if j.get("success"):
                    break
            except Exception:
                time.sleep(2 * (attempt + 1))
        res = j.get("result") or {} if j else {}
        rows += res.get("data") or []
        pages = res.get("pages") or 1
        page += 1
        time.sleep(0.3)
    return rows


def main():
    for ds in DATES:
        out = os.path.join(RAW, f"valuation_{ds}.csv")
        if os.path.exists(out) and os.path.getsize(out) > 1000:
            print("skip", ds, flush=True)
            continue
        rows = fetch(ds)
        if rows:
            pd.DataFrame(rows).to_csv(out, index=False, encoding="utf-8-sig")
        print(ds, len(rows), flush=True)
        time.sleep(0.5)
    print("DONE", flush=True)


if __name__ == "__main__":
    main()

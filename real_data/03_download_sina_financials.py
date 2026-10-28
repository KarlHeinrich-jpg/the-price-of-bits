# -*- coding: utf-8 -*-
"""Per-firm quarterly financial indicators from Sina Finance.

AkShare endpoint: stock_financial_analysis_indicator (all report periods).
One request chain per firm; four workers.
"""
import os
import time
import pandas as pd
import net
from concurrent.futures import ThreadPoolExecutor, as_completed

for k in list(os.environ):
    if "proxy" in k.lower():
        os.environ.pop(k, None)
os.environ["TQDM_DISABLE"] = "1"

import akshare as ak

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(BASE, "real_data", "raw", "sina")
os.makedirs(RAW, exist_ok=True)


def one(code):
    out = os.path.join(RAW, f"{code}.csv")
    if os.path.exists(out) and os.path.getsize(out) > 2000:
        return code, "cached", 0
    for attempt in range(4):
        try:
            df = ak.stock_financial_analysis_indicator(symbol=code, start_year="2017")
            if df is not None and len(df) > 4:
                df.to_csv(out, index=False, encoding="utf-8-sig")
                return code, "ok", len(df)
        except Exception as e:
            err = type(e).__name__
            time.sleep(2 * (attempt + 1))
    return code, "failed", 0


def main():
    codes = pd.read_csv(os.path.join(BASE, "real_data", "sample_codes.csv"),
                        dtype={"SECURITY_CODE": str})["SECURITY_CODE"].str.zfill(6).tolist()
    print("codes", len(codes), flush=True)
    done = 0
    with ThreadPoolExecutor(max_workers=8) as ex:
        futs = {ex.submit(one, c): c for c in codes}
        for f in as_completed(futs):
            code, status, n = f.result()
            done += 1
            print(done, code, status, n, flush=True)
    print("DONE", flush=True)


if __name__ == "__main__":
    main()

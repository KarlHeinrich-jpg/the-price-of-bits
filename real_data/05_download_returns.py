# -*- coding: utf-8 -*-
"""Daily stock returns for the sample and benchmark indices (Sina Finance)."""
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
RAW = os.path.join(BASE, "real_data", "raw", "prices")
os.makedirs(RAW, exist_ok=True)


def prefix(code):
    return ("sh" if code.startswith("6") else "sz") + code


def one(code):
    out = os.path.join(RAW, f"{code}.csv")
    if os.path.exists(out) and os.path.getsize(out) > 500:
        return code, "cached", 0
    for attempt in range(4):
        try:
            df = ak.stock_zh_a_daily(symbol=prefix(code), start_date="20190101",
                                     end_date="20231231", adjust="qfq")
            if df is not None and len(df) > 100:
                df.to_csv(out, index=False, encoding="utf-8-sig")
                return code, "ok", len(df)
        except Exception:
            time.sleep(2 * (attempt + 1))
    return code, "failed", 0


def index_one(sym, tag):
    out = os.path.join(RAW, f"{tag}.csv")
    if os.path.exists(out) and os.path.getsize(out) > 500:
        return tag, "cached", 0
    for attempt in range(4):
        try:
            df = ak.stock_zh_index_daily(symbol=sym)
            df = df[(df["date"] >= "2019-01-01") & (df["date"] <= "2023-12-31")]
            if len(df) > 100:
                df.to_csv(out, index=False, encoding="utf-8-sig")
                return tag, "ok", len(df)
        except Exception:
            time.sleep(2 * (attempt + 1))
    return tag, "failed", 0


def main():
    codes = pd.read_csv(os.path.join(BASE, "real_data", "sample_codes.csv"),
                        dtype={"SECURITY_CODE": str})["SECURITY_CODE"].str.zfill(6).tolist()
    with ThreadPoolExecutor(max_workers=8) as ex:
        futs = {ex.submit(one, c): c for c in codes}
        futs.update({ex.submit(index_one, s, t): t for s, t in
                     [("sh000300", "index_hs300"), ("sh000905", "index_csi500"),
                      ("sz399006", "index_cyb")]})
        for i, f in enumerate(as_completed(futs), 1):
            try:
                tag, status, n = f.result()
            except Exception as e:
                tag, status, n = futs[f], f"error:{type(e).__name__}", 0
            print(i, tag, status, n, flush=True)
    print("DONE", flush=True)


if __name__ == "__main__":
    main()

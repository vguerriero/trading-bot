# ingest/sec_fund.py
"""
Fetch the five most‑recent 10‑K / 10‑Q filings for each symbol
and upsert basic metadata into the `fundamentals` table.
Uses the public SEC “submissions” JSON endpoint (no paid key needed).
Runs once, designed to be invoked weekly by Docker loop.
"""

import os
import json
import asyncio
import datetime as dt
import asyncpg
import requests
import requests_cache
from ops.secret_loader import load_secrets

# ── CONFIG ───────────────────────────────────────────────────────────────
UA = (
    "TradingBot/0.1 (email@example.com) "
    "Need-contact-header-per-SEC"
)  # <- put a real contact email here
HEADERS = {"User-Agent": UA, "Accept-Encoding": "gzip, deflate"}

CIK_MAP_URL = "https://www.sec.gov/files/company_tickers.json"
SUB_URL = "https://data.sec.gov/submissions/CIK{cik}.json"

CACHE_PATH = "/tmp/sec_fund_cache"
CACHE_TTL = 86400  # 24 h

requests_cache.install_cache(CACHE_PATH, expire_after=CACHE_TTL)

load_secrets()  # not required here but keeps pattern consistent

# ── HELPERS ──────────────────────────────────────────────────────────────
def get_cik_map() -> dict[str, str]:
    """Return {ticker: cik} mapping (CIK is 10‑digit zero‑padded str)."""
    r = requests.get(CIK_MAP_URL, headers=HEADERS, timeout=30)
    r.raise_for_status()
    data = r.json()
    return {item["ticker"]: f"{int(item['cik_str']):010d}" for item in data.values()}

CIK_MAP = get_cik_map()

def recent_filings(ticker: str, limit: int = 5) -> list[dict]:
    """Return up to `limit` recent 10‑K/Q filing dicts for ticker."""
    cik = CIK_MAP.get(ticker.upper())
    if not cik:
        print(f"⚠️  No CIK for {ticker}")
        return []

    r = requests.get(SUB_URL.format(cik=cik), headers=HEADERS, timeout=30)
    r.raise_for_status()
    sub = r.json()

    forms   = sub["filings"]["recent"]["form"]
    dates   = sub["filings"]["recent"]["filingDate"]
    accnos  = sub["filings"]["recent"]["accessionNumber"]
    filings = []

    for form, date, acc in zip(forms, dates, accnos):
        if form not in ("10-K", "10-Q"):
            continue
        filings.append(
            {
                "cik": cik,
                "symbol": ticker.upper(),
                "filing_date": date,
                "form": form,
                "accession": acc,
            }
        )
        if len(filings) >= limit:
            break
    return filings

async def store(rows: list[tuple]):
    """Bulk‑upsert rows into fundamentals."""
    if not rows:
        print("No rows to insert.")
        return

    dsn = "postgresql://trader:trader_pw@feature_store:5432/trading"
    pool = await asyncpg.create_pool(dsn, min_size=1, max_size=4)
    sql = """
    INSERT INTO fundamentals
      (cik, symbol, filing_date, fiscal_year,
       revenue, net_income, eps, doc_json)
    VALUES ($1,$2,$3,$4,$5,$6,$7,$8)
    ON CONFLICT DO NOTHING;
    """
    async with pool.acquire() as con:
        await con.executemany(sql, rows)
    await pool.close()

# ── MAIN ─────────────────────────────────────────────────────────────────
async def main():
    symbols = os.getenv("SYMBOL_UNIVERSE", "AAPL,MSFT,NVDA,AMD").split(",")
    batch: list[tuple] = []

    for sym in symbols:
        print(f"🔎 {sym}: fetching recent 10‑K/10‑Q", flush=True)
        for f in recent_filings(sym):
            fy = dt.datetime.fromisoformat(f["filing_date"]).year
            batch.append(
                (
                    f["cik"],
                    sym,
                    f["filing_date"],
                    fy,
                    None,  # revenue placeholder
                    None,  # net_income placeholder
                    None,  # eps placeholder
                    json.dumps(f),
                )
            )

    await store(batch)
    print(f"🏁 Stored {len(batch)} filings", flush=True)

if __name__ == "__main__":
    asyncio.run(main())

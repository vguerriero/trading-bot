# ingest/sec_fund.py

"""
Fetch the five most‑recent 10‑K / 10‑Q filings for each symbol
and upsert basic metadata into the `fundamentals` table.
Uses the SEC “company submissions” JSON feed (no paid key required).
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
UA = "TradingBot/0.1 (contact@example.com)"        # <-- put a real email
HEADERS = {"User-Agent": UA, "Accept-Encoding": "gzip, deflate"}

CIK_MAP_URL = "https://www.sec.gov/files/company_tickers.json"
SUB_URL     = "https://data.sec.gov/submissions/CIK{cik}.json"

CACHE_PATH  = "/tmp/sec_fund_cache"
CACHE_TTL   = 86400  # 24 h

requests_cache.install_cache(CACHE_PATH, expire_after=CACHE_TTL)
load_secrets()  # keeps pattern consistent (no envs needed here)

# ── HELPERS ──────────────────────────────────────────────────────────────
def get_cik_map() -> dict[str, str]:
    """Return {ticker: CIK_10digits} mapping."""
    r = requests.get(CIK_MAP_URL, headers=HEADERS, timeout=30)
    r.raise_for_status()
    data = r.json()
    return {item["ticker"]: f"{int(item['cik_str']):010d}" for item in data.values()}

CIK_MAP = get_cik_map()

def recent_filings(ticker: str, limit: int = 5) -> list[dict]:
    """Return up to `limit` recent 10‑K/Q filings for the ticker."""
    cik = CIK_MAP.get(ticker.upper())
    if not cik:
        print(f"⚠️  No CIK found for {ticker}")
        return []

    r = requests.get(SUB_URL.format(cik=cik), headers=HEADERS, timeout=30)
    r.raise_for_status()
    sub = r.json()

    forms   = sub["filings"]["recent"]["form"]
    dates   = sub["filings"]["recent"]["filingDate"]
    accnos  = sub["filings"]["recent"]["accessionNumber"]

    filings = []
    for form, date_str, acc in zip(forms, dates, accnos):
        if form not in ("10-K", "10-Q"):
            continue
        filings.append(
            dict(
                cik=cik,
                symbol=ticker.upper(),
                filing_date=dt.date.fromisoformat(date_str),
                fiscal_year=dt.date.fromisoformat(date_str).year,
                form=form,
                accession=acc,
            )
        )
        if len(filings) >= limit:
            break
    return filings

async def store(rows: list[tuple]):
    """Bulk‑insert filing rows into fundamentals table."""
    if not rows:
        print("⚠️  No rows to insert.")
        return

    dsn  = "postgresql://trader:trader_pw@feature_store:5432/trading"
    pool = await asyncpg.create_pool(dsn, min_size=1, max_size=4)
    sql  = """
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
            batch.append(
                (
                    f["cik"],
                    f["symbol"],
                    f["filing_date"],     # DATE object
                    f["fiscal_year"],
                    None, None, None,     # rev / NI / EPS placeholders
                    json.dumps(f, default=str),
                )
            )

    await store(batch)
    print(f"🏁 Stored {len(batch)} filings", flush=True)

if __name__ == "__main__":
    asyncio.run(main())

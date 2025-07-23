# ingest/sec_fund.py

"""
Fetch the five most-recent 10-K / 10-Q filings for each symbol
and upsert headline fundamentals into the `fundamentals` table.
Runs once, designed to be invoked weekly by Docker loop.
"""

import os
import json
import asyncio
import asyncpg
import requests
import requests_cache
from ops.secret_loader import load_secrets

# ── config ──────────────────────────────────────────────────────────────
API = "https://api.sec-api.io"
# Cache responses for 24 h to avoid repeated calls during dev/debug
requests_cache.install_cache("/tmp/sec_fund_cache", expire_after=86400)

load_secrets()  # pulls SEC_API_KEY into env

def filings(symbol: str) -> list[dict]:
    """Return the 5 latest 10-K/Q filing metadata dicts for a ticker."""
    params = {
        "token": os.environ["SEC_API_KEY"],
        "query": {
            "query": {
                "query_string": {
                    "query": f'ticker:{symbol} AND formType:("10-K","10-Q")'
                }
            }
        },
        "from": 0,
        "size": 5,
        "sort": [{"filedAt": {"order": "desc"}}],
    }
    resp = requests.post(f"{API}/filings", json=params, timeout=30)
    resp.raise_for_status()
    return resp.json().get("filings", [])

def extract_numbers(xbrl_url: str):
    """
    Placeholder — XBRL parsing skipped due to compatibility issues.
    Returns None for revenue, net_income, eps.
    """
    print(f"⚠️  Skipping XBRL parse for {xbrl_url}", flush=True)
    return None, None, None

async def store(rows: list[tuple]):
    """Bulk-upsert filing rows into the fundamentals table."""
    dsn = "postgresql://trader:trader_pw@feature_store:5432/trading"
    pool = await asyncpg.create_pool(dsn, min_size=1, max_size=4)
    sql = """
    INSERT INTO fundamentals
      (cik, symbol, filing_date, fiscal_year, revenue, net_income, eps, doc_json)
    VALUES($1, $2, $3, $4, $5, $6, $7, $8)
    ON CONFLICT DO NOTHING;
    """
    async with pool.acquire() as conn:
        await conn.executemany(sql, rows)
    await pool.close()

async def main():
    symbols = os.getenv("SYMBOL_UNIVERSE", "AAPL,MSFT,NVDA,AMD").split(",")
    batch = []
    for sym in symbols:
        print(f"🔎 {sym}: fetching filings", flush=True)
        for f in filings(sym):
            rev, ni, eps = extract_numbers(f.get("linkToXbrl", ""))
            filing_date = f.get("filedAt", "")[:10]  # YYYY-MM-DD
            batch.append((
                f.get("cik"),
                sym,
                filing_date,
                f.get("fiscalYear"),
                rev,
                ni,
                eps,
                json.dumps(f),
            ))
    await store(batch)
    print(f"🏁 Stored {len(batch)} filings", flush=True)

if __name__ == "__main__":
    asyncio.run(main())

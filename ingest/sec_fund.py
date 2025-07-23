"""
Fetch the five most‑recent 10‑K / 10‑Q filings for each symbol
and upsert headline fundamentals into the `fundamentals` table.
Runs once, designed to be invoked weekly by Docker loop.
"""

import os, json, asyncio, datetime as dt
import asyncpg, requests, requests_cache
from arelle import Cntlr, ModelManager
from ops.secret_loader import load_secrets

# ── config ──────────────────────────────────────────────────────────────
API   = "https://api.sec-api.io"
FIELDS = ["us-gaap:Revenues", "us-gaap:NetIncomeLoss", "us-gaap:EarningsPerShareBasic"]

# 24 h cache so repeated debug runs don’t hammer SEC‑API
requests_cache.install_cache("/tmp/sec_fund_cache", expire_after=86400)

load_secrets()  # pulls SEC_API_KEY into env

def filings(symbol: str):
    """Return the 5 latest 10‑K/Q filing metadata dicts for a ticker."""
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
    r = requests.post(f"{API}/filings", json=params, timeout=30)
    r.raise_for_status()
    return r.json().get("filings", [])

def extract_numbers(xbrl_url: str):
    """Pull Revenue, Net Income, EPS (basic) from XBRL, return tuple."""
    try:
        cntlr  = Cntlr.Cntlr(logFileName="/dev/null", logFileMode="w")
        model  = ModelManager.load(cntlr, url=xbrl_url)
    except Exception as e:
        print(f"⚠️  XBRL load failed: {e}")
        return (None, None, None)

    def first_fact(qname_str):
        qn = model.qname(qname_str)
        return (
            model.factsByQname[qn][0].value
            if qn in model.factsByQname and model.factsByQname[qn]
            else None
        )

    rev  = first_fact(FIELDS[0])
    ni   = first_fact(FIELDS[1])
    eps  = first_fact(FIELDS[2])
    return rev, ni, eps

async def store(rows):
    dsn  = "postgresql://trader:trader_pw@feature_store:5432/trading"
    pool = await asyncpg.create_pool(dsn, min_size=1, max_size=4)
    sql  = """
    INSERT INTO fundamentals
      (cik,symbol,filing_date,fiscal_year,revenue,net_income,eps,doc_json)
    VALUES($1,$2,$3,$4,$5,$6,$7,$8)
    ON CONFLICT DO NOTHING;
    """
    async with pool.acquire() as con:
        await con.executemany(sql, rows)
    await pool.close()

async def main():
    symbols = os.getenv("SYMBOL_UNIVERSE", "AAPL,MSFT,NVDA,AMD").split(",")
    batch   = []

    for sym in symbols:
        print(f"🔎 {sym}: fetching filing list", flush=True)
        for f in filings(sym):
            rev, ni, eps = extract_numbers(f["linkToXbrl"])
            filing_date  = f["filedAt"][:10]   # YYYY‑MM‑DD
            batch.append(
                (
                    f["cik"],
                    sym,
                    filing_date,
                    f["fiscalYear"],
                    rev,
                    ni,
                    eps,
                    json.dumps(f),
                )
            )

    await store(batch)
    print(f"🏁 Stored {len(batch)} filings", flush=True)

if __name__ == "__main__":
    asyncio.run(main())

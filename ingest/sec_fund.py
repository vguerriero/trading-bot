import os, json, asyncio, asyncpg, requests, datetime
from arelle import Cntlr, ModelManager
from ops.secret_loader import load_secrets

API = "https://api.sec-api.io"
load_secrets()

def filings(symbol):
    params = {
        "token": os.environ["SEC_API_KEY"],
        "query": {"query": {"query_string": {"query": f'ticker:{symbol} AND formType:("10-K","10-Q")'}}},
        "from": 0, "size": 5, "sort": [{"filedAt": {"order": "desc"}}]
    }
    return requests.get(f"{API}/filings", json=params).json()["filings"]

def extract_numbers(xbrl_url):
    cntlr = Cntlr.Cntlr()
    model = ModelManager.load(cntlr, url=xbrl_url)
    ns = model.qname("us-gaap:Revenues")
    rev = model.factsByQname[ns][0].value if ns in model.factsByQname else None
    # ... similar for NI & EPS ...
    return rev, None, None

async def store(rows):
    pool = await asyncpg.create_pool("postgresql://trader:trader_pw@feature_store:5432/trading")
    sql = """INSERT INTO fundamentals(cik,symbol,filing_date,fiscal_year,revenue,net_income,eps,doc_json)
             VALUES($1,$2,$3,$4,$5,$6,$7,$8)
             ON CONFLICT DO NOTHING"""
    async with pool.acquire() as con:
        await con.executemany(sql, rows)
    await pool.close()

async def main():
    symbols = os.getenv("SYMBOL_UNIVERSE").split(",")
    batch = []
    for sym in symbols:
        for f in filings(sym):
            rev, ni, eps = extract_numbers(f["linkToXbrl"])
            filing_date = f["filedAt"][:10]
            batch.append((f["cik"], sym, filing_date, f["fiscalYear"], rev, ni, eps, json.dumps(f)))
    await store(batch)

if __name__ == "__main__":
    asyncio.run(main())
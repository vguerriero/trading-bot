# ingest/trends_job.py
"""
Daily Google Trends scraper -> alt_trends table.
Grabs the last 12 months of interest‑over‑time data per keyword.
"""

import asyncio, asyncpg
from datetime import date
from pytrends.request import TrendReq

KEYWORDS = ["buy stocks", "inflation"]
POOL_DSN = "postgresql://trader:trader_pw@feature_store:5432/trading"

async def main():
    pg = await asyncpg.create_pool(POOL_DSN, min_size=1, max_size=4)
    pt = TrendReq(hl="en-US", tz=0)

    for kw in KEYWORDS:
        print(f"🔄 Pulling trends for '{kw}'", flush=True)
        pt.build_payload([kw], timeframe="today 12-m")   # last 12 months
        df = pt.interest_over_time()
        if df.empty:
            print(f"⚠️  No data for '{kw}'")
            continue

        df = df.reset_index()
        df = df[df["isPartial"] == False]                # drop partial weeks
        rows = [
            (ts.date(), kw, int(val))
            for ts, val in zip(df["date"], df[kw])
            if val > 0
        ]

        sql = """INSERT INTO alt_trends(date, keyword, score)
                 VALUES($1,$2,$3) ON CONFLICT DO NOTHING"""
        async with pg.acquire() as con:
            await con.executemany(sql, rows)

        print(f"✅ Stored {len(rows)} rows for '{kw}'", flush=True)

    await pg.close()
    print("🏁 trends_job complete", flush=True)

if __name__ == "__main__":
    asyncio.run(main())

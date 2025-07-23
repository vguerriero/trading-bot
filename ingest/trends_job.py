# ingest/trends_job.py
"""
Daily Google Trends scraper → alt_trends table.
Fetches the last 12 months of interest‑over‑time data for each keyword.
"""

from pytrends.request import TrendReq
import asyncpg, asyncio
import datetime as dt

KEYWORDS = ["buy stocks", "inflation"]          # add more as needed
POOL_DSN  = "postgresql://trader:trader_pw@feature_store:5432/trading"

async def main():
    today   = dt.date.today()
    start   = today - dt.timedelta(days=365)
    pg      = await asyncpg.create_pool(POOL_DSN, min_size=1, max_size=4)
    pt      = TrendReq(hl="en-US", tz=0)        # no auth required

    for kw in KEYWORDS:
        print(f"🔄 Pulling trends for '{kw}'", flush=True)
        df = pt.get_historical_interest(
            [kw],
            year_start=start.year,
            month_start=start.month,
            day_start=start.day,
            hour_start=0,
            year_end=today.year,
            month_end=today.month,
            day_end=today.day,
            hour_end=0,
            cat=0,
            sleep=0,
        )

        # df index = Timestamp; column = kw; convert to list of tuples
        rows = [
            (ts.date(), kw, int(val))
            for ts, val in df[kw].items()
            if val != 0                                   # drop zeros
        ]

        sql = """
        INSERT INTO alt_trends(date, keyword, score)
        VALUES($1,$2,$3) ON CONFLICT DO NOTHING
        """
        async with pg.acquire() as conn:
            await conn.executemany(sql, rows)

        print(f"✅ Stored {len(rows)} rows for '{kw}'", flush=True)

    await pg.close()
    print("🏁 trends_job complete", flush=True)

if __name__ == "__main__":
    asyncio.run(main())
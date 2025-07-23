# ingest/candles_job.py

import os
import pandas as pd
import asyncpg
import asyncio
from datetime import date, timedelta
import alpaca_trade_api as tradeapi
from ops.secret_loader import load_secrets

async def store(df, pool):
    sql = """
    INSERT INTO candles(date, symbol, open, high, low, close, volume)
    VALUES($1, $2, $3, $4, $5, $6, $7)
    ON CONFLICT (date, symbol) DO UPDATE
      SET open=EXCLUDED.open,
          high=EXCLUDED.high,
          low=EXCLUDED.low,
          close=EXCLUDED.close,
          volume=EXCLUDED.volume;
    """
    async with pool.acquire() as conn:
        records = [
            (row.date, row.symbol, row.open, row.high, row.low, row.close, row.volume)
            for row in df.itertuples(index=False)
        ]
        await conn.executemany(sql, records)

async def run():
    load_secrets()
    api = tradeapi.REST()  # reads ALPACA_PAPER_KEY / SECRET from env
    symbols = os.getenv("SYMBOL_UNIVERSE", "AAPL,MSFT,NVDA,AMD").split(",")
    end = date.today()
    start = end - timedelta(days=365*5)  # last 5 years

    pool = await asyncpg.create_pool(
        "postgresql://trader:trader_pw@feature_store:5432/trading",
        min_size=1, max_size=4
    )

    for sym in symbols:
        barset = api.get_bars(sym, "1Day",
                              start=start.isoformat(),
                              end=end.isoformat()).df
        if barset.empty:
            continue

        barset["symbol"] = sym
        barset.rename(columns={
            "t": "date", "o": "open", "h": "high",
            "l": "low", "c": "close", "v": "volume"
        }, inplace=True)
        df = barset[["date","symbol","open","high","low","close","volume"]]

        await store(df, pool)

    await pool.close()

if __name__ == "__main__":
    asyncio.run(run())

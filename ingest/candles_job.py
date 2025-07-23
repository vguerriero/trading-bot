import os, pandas as pd
import alpaca_trade_api as tradeapi
import asyncpg, asyncio
from datetime import date, timedelta
from ops.secret_loader import load_secrets

async def store(df, pool):
    sql = """INSERT INTO candles(date,symbol,open,high,low,close,volume)
             VALUES($1,$2,$3,$4,$5,$6,$7)
             ON CONFLICT (date,symbol) DO UPDATE
             SET open=EXCLUDED.open, high=EXCLUDED.high,
                 low=EXCLUDED.low, close=EXCLUDED.close,
                 volume=EXCLUDED.volume"""
    async with pool.acquire() as con:
        await con.executemany(sql, df.itertuples(index=False, name=None))

async def run():
    load_secrets()
    api = tradeapi.REST()
    symbols = os.getenv("SYMBOL_UNIVERSE").split(",")
    end = date.today()
    start = end - timedelta(days=365*5)
    pool = await asyncpg.create_pool("postgresql://trader:trader_pw@feature_store:5432/trading")
    for sym in symbols:
        barset = api.get_bars(sym, "1Day", start=start, end=end).df
        barset["symbol"] = sym
        barset.rename(columns={"t":"date","o":"open","h":"high",
                               "l":"low","c":"close","v":"volume"},inplace=True)
        barset = barset[["date","symbol","open","high","low","close","volume"]]
        await store(barset, pool)
    await pool.close()

if __name__ == "__main__":
    asyncio.run(run())
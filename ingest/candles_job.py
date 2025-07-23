import os
import pandas as pd
import alpaca_trade_api as tradeapi
import asyncpg
import asyncio
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
    # load secrets (including ALPACA_PAPER_KEY and ALPACA_PAPER_SECRET)
    load_secrets()

    # initialize Alpaca REST client with paper-trading credentials
    key    = os.environ["ALPACA_PAPER_KEY"]
    secret = os.environ["ALPACA_PAPER_SECRET"]
    base_url = "https://paper-api.alpaca.markets"
    api = tradeapi.REST(key, secret, base_url)

    symbols = os.getenv("SYMBOL_UNIVERSE").split(",")
    end = date.today()
    start = end - timedelta(days=365 * 5)

    pool = await asyncpg.create_pool(
        "postgresql://trader:trader_pw@feature_store:5432/trading"
    )

    for sym in symbols:
        try:
            # use 'iex' feed to stay within Basic plan limits
            barset = api.get_bars(
                sym,
                "1Day",
                start=start,
                end=end,
                feed="iex"
            ).df
        except tradeapi.rest.APIError as e:
            print(f"[ERROR] fetching bars for {sym}: {e}", flush=True)
            continue

        barset["symbol"] = sym
        barset.rename(
            columns={
                "t": "date",
                "o": "open",
                "h": "high",
                "l": "low",
                "c": "close",
                "v": "volume",
            },
            inplace=True,
        )
        barset = barset[["date", "symbol", "open", "high", "low", "close", "volume"]]
        await store(barset, pool)

    await pool.close()

if __name__ == "__main__":
    asyncio.run(run())

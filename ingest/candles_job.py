# ingest/candles_job.py

import os
import pandas as pd
import asyncpg
import asyncio
from datetime import date, timedelta
import alpaca_trade_api as tradeapi
from ops.secret_loader import load_secrets

async def store(df: pd.DataFrame, pool: asyncpg.Pool):
    sql = """
    INSERT INTO candles(date, symbol, open, high, low, close, volume)
    VALUES($1, $2, $3, $4, $5, $6, $7)
    ON CONFLICT (date, symbol) DO UPDATE
      SET open      = EXCLUDED.open,
          high      = EXCLUDED.high,
          low       = EXCLUDED.low,
          close     = EXCLUDED.close,
          volume    = EXCLUDED.volume;
    """
    async with pool.acquire() as conn:
        records = [
            (row.date, row.symbol, row.open, row.high, row.low, row.close, row.volume)
            for row in df.itertuples(index=False)
        ]
        await conn.executemany(sql, records)

async def run():
    load_secrets()

    # map secrets to alpaca_trade_api env vars
    os.environ["APCA_API_KEY_ID"]     = os.environ["ALPACA_PAPER_KEY"]
    os.environ["APCA_API_SECRET_KEY"] = os.environ["ALPACA_PAPER_SECRET"]
    os.environ.setdefault(
        "APCA_API_BASE_URL",
        "https://paper-api.alpaca.markets"
    )

    api = tradeapi.REST()  # now picks up APCA_API_KEY_ID/SECRET
    symbols = os.getenv("SYMBOL_UNIVERSE", "AAPL,MSFT,NVDA,AMD").split(",")
    end = date.today()
    start = end - timedelta(days=365*5)

    pool = await asyncpg.create_pool(
        "postgresql://trader:trader_pw@feature_store:5432/trading",
        min_size=1, max_size=4
    )

    for sym in symbols:
        print(f"▶️ Fetching {sym} from {start} to {end}", flush=True)
        try:
            barset = api.get_bars(
                sym, "1Day",
                start=start.isoformat(),
                end=end.isoformat()
            ).df
        except Exception as e:
            print(f"❌ Error fetching {sym}: {e}", flush=True)
            continue

        if barset.empty:
            print(f"⚠️ No data for {sym}", flush=True)
            continue

        df = barset.reset_index()
        idx_col = df.columns[0]  # timestamp column
        df.rename(columns={idx_col: "date"}, inplace=True)
        df["symbol"] = sym
        df = df[["date", "symbol", "open", "high", "low", "close", "volume"]]

        await store(df, pool)

    await pool.close()

if __name__ == "__main__":
    asyncio.run(run())

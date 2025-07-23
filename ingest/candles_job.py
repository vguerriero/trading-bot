# ingest/candles_job.py

import os
import pandas as pd
import asyncpg
import asyncio
from datetime import date, timedelta
import alpaca_trade_api as tradeapi
from ops.secret_loader import load_secrets

async def store(df: pd.DataFrame, pool: asyncpg.Pool) -> None:
    """Bulk-upsert a DataFrame of daily bars into the candles table."""
    sql = """
    INSERT INTO candles(date, symbol, open, high, low, close, volume)
    VALUES($1,$2,$3,$4,$5,$6,$7)
    ON CONFLICT (date, symbol) DO UPDATE
      SET open   = EXCLUDED.open,
          high   = EXCLUDED.high,
          low    = EXCLUDED.low,
          close  = EXCLUDED.close,
          volume = EXCLUDED.volume;
    """
    async with pool.acquire() as conn:
        await conn.executemany(
            sql,
            [
                (r.date, r.symbol, r.open, r.high, r.low, r.close, r.volume)
                for r in df.itertuples(index=False)
            ],
        )

async def run() -> None:
    """Back-fill (or refresh) 1-day candles for the configured symbol universe."""
    load_secrets()  # pulls ALPACA_PAPER_KEY / _SECRET into env

    key = os.getenv("ALPACA_PAPER_KEY")
    sec = os.getenv("ALPACA_PAPER_SECRET")
    if not key or not sec:
        raise RuntimeError("Missing ALPACA_PAPER_KEY / ALPACA_PAPER_SECRET")

    # Initialize REST client (no data_feed arg here)
    api = tradeapi.REST(
        key_id=key,
        secret_key=sec,
        base_url="https://paper-api.alpaca.markets",
        api_version="v2",
    )

    symbols = os.getenv("SYMBOL_UNIVERSE", "AAPL,MSFT,NVDA,AMD").split(",")
    end = date.today()
    start = end - timedelta(days=365 * 5)

    pool = await asyncpg.create_pool(
        "postgresql://trader:trader_pw@feature_store:5432/trading",
        min_size=1,
        max_size=4,
    )

    for sym in symbols:
        print(f"▶️ Fetching {sym} {start}→{end}", flush=True)
        try:
            barset = api.get_bars(
                sym,
                "1Day",
                start=start.isoformat(),
                end=end.isoformat(),
                limit=None,
                adjustment="raw",
                feed="iex",         # ensure free IEX data
            ).df
        except Exception as exc:
            print(f"❌ {sym}: {exc}", flush=True)
            continue

        if barset.empty:
            print(f"⚠️  No data returned for {sym}", flush=True)
            continue

        df = barset.reset_index()
        df.rename(columns={df.columns[0]: "date"}, inplace=True)
        df["symbol"] = sym
        df = df[["date", "symbol", "open", "high", "low", "close", "volume"]]

        await store(df, pool)
        print(f"✅ Stored {len(df):,} rows for {sym}", flush=True)

    await pool.close()
    print("🏁 Candle back-fill complete", flush=True)

if __name__ == "__main__":
    asyncio.run(run())

import os
from decimal import Decimal

import asyncpg
from alpaca.data.live import StockDataStream
from ops.secret_loader import load_secrets

# ─── 1. Load secrets ─────────────────────────────────────────────────────────────
load_secrets()
API_KEY = os.environ["ALPACA_PAPER_KEY"]
API_SEC = os.environ["ALPACA_PAPER_SECRET"]

DB_DSN  = "postgresql://trader:trader_pw@feature_store:5432/trading"
SYMBOLS = os.getenv("SYMBOL_UNIVERSE", "AAPL,MSFT,NVDA,AMD").split(",")

# ─── 2. Lazy-init pool & SQL ──────────────────────────────────────────────────────
_pg_pool = None
INSERT_SQL = """
    INSERT INTO ticks(ts, symbol, bid, ask, last, size)
    VALUES($1, $2, $3, $4, $5, $6)
    ON CONFLICT DO NOTHING
"""

async def _ensure_pool():
    global _pg_pool
    if _pg_pool is None:
        _pg_pool = await asyncpg.create_pool(DB_DSN, min_size=1, max_size=4)

async def quote_handler(q):
    """Called by Alpaca on each quote update—logs + writes to Postgres."""
    await _ensure_pool()

    bid = Decimal(str(q.bid_price))
    ask = Decimal(str(q.ask_price))
    mid = (bid + ask) / 2
    size = (q.bid_size or 0) + (q.ask_size or 0)

    # log it so we know it’s alive
    print(f"[QUOTE] {q.symbol} @ {q.timestamp}  bid={bid}  ask={ask}  mid={mid}  size={size}", flush=True)

    async with _pg_pool.acquire() as conn:
        await conn.execute(
            INSERT_SQL,
            q.timestamp,
            q.symbol,
            bid,
            ask,
            mid,
            size,
        )

# ─── 3. Subscribe & run ─────────────────────────────────────────────────────────
def main():
    print(f"→ market_ws starting, subscribing to {SYMBOLS}", flush=True)
    stream = StockDataStream(API_KEY, API_SEC, feed="iex")
    stream.subscribe_quotes(quote_handler, *SYMBOLS)
    stream.run()  # blocking

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("market_ws stopped")

import os
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

async def quote_handler(q):
    """Called by Alpaca on each quote update—logs + writes to Postgres."""
    global _pg_pool
    if _pg_pool is None:
        _pg_pool = await asyncpg.create_pool(DB_DSN, min_size=1, max_size=4)

    # log it so we know it’s alive
    print(f"[QUOTE] {q.symbol} @ {q.timestamp}  bid={q.bid_price}  ask={q.ask_price}  last={q.last_price}", flush=True)

    async with _pg_pool.acquire() as conn:
        await conn.execute(
            INSERT_SQL,
            q.timestamp,
            q.symbol,
            q.bid_price,
            q.ask_price,
            q.last_price,
            q.size,
        )

# ─── 3. Subscribe & run ─────────────────────────────────────────────────────────
def main():
    print(f"→ market_ws starting, subscribing to {SYMBOLS}", flush=True)
    stream = StockDataStream(API_KEY, API_SEC)
    stream.subscribe_quotes(quote_handler, *SYMBOLS)
    stream.run()  # blocking

if __name__ == "__main__":
    main()

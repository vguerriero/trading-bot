import os
import asyncpg
from alpaca.data.live import StockDataStream
from ops.secret_loader import load_secrets

# ----------------------------------------------------------------------
# 1. Load secrets and basic settings
# ----------------------------------------------------------------------
load_secrets()

DB_DSN   = "postgresql://trader:trader_pw@feature_store:5432/trading"
SYMBOLS  = os.getenv("SYMBOL_UNIVERSE", "AAPL,MSFT,NVDA,AMD").split(",")

API_KEY  = os.environ["ALPACA_PAPER_KEY"]
API_SEC  = os.environ["ALPACA_PAPER_SECRET"]

# ----------------------------------------------------------------------
# 2. Lazy‑initialised async‑pg pool (created on first quote)
# ----------------------------------------------------------------------
_pg_pool = None
INSERT_SQL = """
    INSERT INTO ticks(ts, symbol, bid, ask, last, size)
    VALUES($1,$2,$3,$4,$5,$6)
    ON CONFLICT DO NOTHING
"""

async def quote_handler(q):
    """Runs inside Alpaca’s event loop; writes each quote to Postgres."""
    global _pg_pool
    if _pg_pool is None:                       # create pool only once
        _pg_pool = await asyncpg.create_pool(DB_DSN, min_size=1, max_size=4)

    async with _pg_pool.acquire() as con:
        await con.execute(
            INSERT_SQL,
            q.timestamp,
            q.symbol,
            q.bid_price,
            q.ask_price,
            q.last_price,
            q.size,
        )

# ----------------------------------------------------------------------
# 3. Wire up stream and block forever
# ----------------------------------------------------------------------
def main() -> None:
    stream = StockDataStream(API_KEY, API_SEC)
    stream.subscribe_quotes(quote_handler, *SYMBOLS)   # note *SYMBOLS
    stream.run()                                       # blocking call

if __name__ == "__main__":
    main()

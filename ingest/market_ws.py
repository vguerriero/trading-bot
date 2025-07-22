import os
import asyncio
import asyncpg
from alpaca.data.live import StockDataStream
from ops.secret_loader import load_secrets

# Load secrets from AWS SSM into environment
load_secrets()

# Database connection string
DB_DSN = "postgresql://trader:trader_pw@feature_store:5432/trading"
# Symbols to subscribe to (comma-separated in ENV)
SYMBOLS = os.getenv("SYMBOL_UNIVERSE", "AAPL,MSFT,NVDA,AMD").split(",")

def main():
    # Create and set a dedicated event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # Initialize asyncpg connection pool
    pool = loop.run_until_complete(
        asyncpg.create_pool(DB_DSN, min_size=1, max_size=4)
    )

    # Initialize Alpaca WebSocket stream
    stream = StockDataStream(
        os.environ["ALPACA_PAPER_KEY"],
        os.environ["ALPACA_PAPER_SECRET"]
    )

    # Handler schedules insert tasks onto our event loop
    def handler(q):
        loop.create_task(
            pool.execute(
                """
                INSERT INTO ticks(ts, symbol, bid, ask, last, size)
                VALUES($1, $2, $3, $4, $5, $6)
                ON CONFLICT DO NOTHING
                """,
                q.timestamp,
                q.symbol,
                q.bid_price,
                q.ask_price,
                q.last_price,
                q.size
            )
        )

    # Subscribe to quote updates for each symbol
    for sym in SYMBOLS:
        stream.subscribe_quotes(handler, sym)

    # Run the stream (blocks forever, using our event loop)
    stream.run()


if __name__ == "__main__":
    main()

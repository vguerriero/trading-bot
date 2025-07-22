import asyncio, os, json, asyncpg
from alpaca.data.live import StockDataStream
from ops.secret_loader import load_secrets

load_secrets()
DB_DSN = "postgresql://trader:trader_pw@feature_store:5432/trading"
SYMBOLS = os.getenv("SYMBOL_UNIVERSE", "AAPL,MSFT,NVDA,AMD").split(",")

async def main():
    pool = await asyncpg.create_pool(DB_DSN, min_size=1, max_size=4)
    stream = StockDataStream(os.environ["ALPACA_PAPER_KEY"],
                             os.environ["ALPACA_PAPER_SECRET"])

    async def handler(q):
        sql = """INSERT INTO ticks(ts,symbol,bid,ask,last,size)
                 VALUES($1,$2,$3,$4,$5,$6)
                 ON CONFLICT DO NOTHING"""
        async with pool.acquire() as con:
            await con.execute(sql, q.timestamp, q.symbol, q.bid_price,
                              q.ask_price, q.last_price, q.size)

    for sym in SYMBOLS:
        stream.subscribe_quotes(handler, sym)

    await stream.run()

if __name__ == "__main__":
    asyncio.run(main())
# ingest/news_stream.py  (N L T K version, no torch/transformers)

import os, re, asyncio, asyncpg, requests, nltk
from datetime import datetime, timezone
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from ops.secret_loader import load_secrets

# download the VADER lexicon once inside the container
nltk.download("vader_lexicon", quiet=True)
sia = SentimentIntensityAnalyzer()

load_secrets()  # NEWSDATA_API_KEY → env

DB  = "postgresql://trader:trader_pw@feature_store:5432/trading"
API = (
    f"https://newsdata.io/api/1/news?apikey={os.environ['NEWSDATA_API_KEY']}"
    "&language=en&domain=seekingalpha.com,finance.yahoo.com"
)

SQL = """INSERT INTO news(ts,source,headline,symbol,sentiment,url)
         VALUES($1,$2,$3,$4,$5,$6) ON CONFLICT DO NOTHING"""

TICKER = re.compile(r"\b[A-Z]{2,5}\b")

async def store(pool, row):
    await pool.execute(SQL, *row)

async def stream():
    pool = await asyncpg.create_pool(DB)
    print("📰 news_stream started", flush=True)

    while True:
        js = requests.get(API, timeout=30).json()
        for art in js.get("results", []):
            ts   = datetime.fromisoformat(art["pubDate"]).replace(tzinfo=timezone.utc)
            head = art["title"] or ""
            syms = list({s for s in TICKER.findall(head)})
            score = sia.polarity_scores(head)["compound"]  # –1 … +1

            row = (ts, art["source_id"], head, syms, round(score, 4), art["link"])
            await store(pool, row)
        await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(stream())

# ingest/news_stream.py  (robust NLTK version)

import os, re, asyncio, asyncpg, requests, nltk
from datetime import datetime, timezone
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from ops.secret_loader import load_secrets

nltk.download("vader_lexicon", quiet=True)
sia = SentimentIntensityAnalyzer()

load_secrets()  # loads NEWSDATA_API_KEY → env

DB  = "postgresql://trader:trader_pw@feature_store:5432/trading"
API = (
    f"https://newsdata.io/api/1/news?apikey={os.environ['NEWSDATA_API_KEY']}"
    "&language=en&domain=seekingalpha.com,finance.yahoo.com"
)

SQL = """INSERT INTO news(ts,source,headline,symbol,sentiment,url)
         VALUES($1,$2,$3,$4,$5,$6) ON CONFLICT DO NOTHING"""

TICKER_RE = re.compile(r"\b[A-Z]{2,5}\b")

async def store(pool, row):
    await pool.execute(SQL, *row)

def parse_date(s):
    try:
        return datetime.fromisoformat(s).replace(tzinfo=timezone.utc)
    except Exception:
        return datetime.utcnow().replace(tzinfo=timezone.utc)

async def stream():
    pool = await asyncpg.create_pool(DB)
    print("📰 news_stream started", flush=True)

    while True:
        try:
            js = requests.get(API, timeout=30).json()
            for art in js.get("results", []):
                if not isinstance(art, dict):
                    continue  # skip unexpected strings/objects

                head = art.get("title") or ""
                if not head:
                    continue

                ts     = parse_date(art.get("pubDate", ""))
                src    = art.get("source_id", "newsdata")
                syms   = list({m for m in TICKER_RE.findall(head)})
                score  = round(sia.polarity_scores(head)["compound"], 4)
                url    = art.get("link", "")

                await store(pool, (ts, src, head, syms, score, url))
        except Exception as e:
            print(f"⚠️  news_stream error: {e}", flush=True)

        await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(stream())

# ingest/news_stream.py
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
    "&language=en"
    # removed domain filter
)

SQL = """INSERT INTO news(ts,source,headline,symbol,sentiment,url)
         VALUES($1,$2,$3,$4,$5,$6) ON CONFLICT DO NOTHING"""

TICKER_RE = re.compile(r"\b[A-Z]{2,5}\b")

async def store(pool, row):
    await pool.execute(SQL, *row)

def parse_date(s):
    try:
        return datetime.fromisoformat(s).replace(tzinfo=timezone.utc)
    except:
        return datetime.utcnow().replace(tzinfo=timezone.utc)

async def stream():
    pool = await asyncpg.create_pool(DB)
    print("📰 news_stream started", flush=True)

    while True:
        try:
            js = requests.get(API, timeout=30).json()
            results = js.get("results", [])
            print(f"🔄 Fetched {len(results)} articles", flush=True)
            for art in results:
                if not isinstance(art, dict): continue
                title = art.get("title") or ""
                if not title: continue

                ts    = parse_date(art.get("pubDate",""))
                src   = art.get("source_id","newsdata")
                syms  = list({m for m in TICKER_RE.findall(title)})
                score = sia.polarity_scores(title)["compound"]
                url   = art.get("link","")

                await store(pool, (ts, src, title, syms, round(score,4), url))
            print("✅ Batch stored", flush=True)
        except Exception as e:
            print(f"⚠️  Error: {e}", flush=True)

        await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(stream())

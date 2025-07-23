# ingest/news_stream.py
import os, re, time, asyncio, asyncpg, requests
from datetime import datetime, timezone
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from ops.secret_loader import load_secrets

# ── Init ───────────────────────────────────────────────────────────────
load_secrets()                                   # loads NEWSDATA_API_KEY → env
tok = AutoTokenizer.from_pretrained(
    "cardiffnlp/twitter-roberta-base-sentiment-latest"
)
mdl = AutoModelForSequenceClassification.from_pretrained(
    "cardiffnlp/twitter-roberta-base-sentiment-latest"
)

DB  = "postgresql://trader:trader_pw@feature_store:5432/trading"
API = f"https://newsdata.io/api/1/news?apikey={os.environ['NEWSDATA_API_KEY']}" \
      "&language=en&domain=seekingalpha.com,finance.yahoo.com"

TICKER_RE = re.compile(r"\b[A-Z]{2,5}\b")        # naïve ticker scrape

SQL = """INSERT INTO news(ts,source,headline,symbol,sentiment,url)
         VALUES($1,$2,$3,$4,$5,$6)
         ON CONFLICT DO NOTHING"""

# ── Main loop ───────────────────────────────────────────────────────────
async def store(pool, row):
    await pool.execute(SQL, *row)

async def stream():
    pool = await asyncpg.create_pool(DB)
    print("📰 news_stream started", flush=True)

    while True:
        try:
            js = requests.get(API, timeout=30).json()
            for art in js.get("results", []):
                headline = art["title"] or ""
                symbols  = list({s for s in TICKER_RE.findall(headline) if len(s) <= 5})
                inputs   = tok(headline, return_tensors="pt", truncation=True)
                score    = mdl(**inputs).logits.softmax(-1)[0][2].item()  # Positive prob

                row = (
                    datetime.fromisoformat(art["pubDate"]).replace(tzinfo=timezone.utc),
                    art["source_id"],
                    headline,
                    symbols,                  # TEXT[] column
                    round(score, 4),
                    art["link"],
                )
                await store(pool, row)
            await asyncio.sleep(60)
        except Exception as e:
            print(f"⚠️  news_stream error: {e}", flush=True)
            await asyncio.sleep(30)

if __name__ == "__main__":
    asyncio.run(stream())
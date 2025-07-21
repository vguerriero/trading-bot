# Trading Bot 2025

This repository contains the foundation for an AI‑driven day trading bot designed to meet configurable daily profit targets while enforcing strict risk controls.

---

## Project Layout

```
ingest/       # Data ingestion modules (market data, news, alt‑data)
models/       # Machine learning and RL model definitions, training scripts
strategies/   # Baseline trading strategies (VWAP scalper, ORB breakout)
ops/          # Orchestration: entrypoint (ops/main.py), monitoring config
tests/        # Unit and sanity tests
docs/         # Documentation: regulations, policies, memos, logs
```

---

## Getting Started

1. **Clone the repo**
   ```bash
git clone git@github.com:<your-user>/trading-bot.git
cd trading-bot
```  
2. **Install dependencies** (using Poetry)
   ```bash
poetry install
```  
3. **Run the entrypoint**
   ```bash
poetry run python -m ops.main
```  
   You should see the "Trading‑bot framework online!" message.
4. **Run tests**
   ```bash
poetry run pytest -q
```

---

## Docker‑Compose (local dev)

Start the full local stack (PostgreSQL, Redis, Prometheus, Grafana, ingestor stub):
```bash
docker compose up --build
```

Access services:
- Grafana: http://localhost:3000 (admin/changeme)
- Prometheus: http://localhost:9090
- Postgres: psql -h localhost -U trader trading

---

*Phase 2.1 complete: repository skeleton in place.*
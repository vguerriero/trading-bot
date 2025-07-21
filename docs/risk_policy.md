# Trading‑Bot Risk Policy (v1.0)

**Max daily drawdown:** 2 % of account equity.  
**Kill switch triggers:**  
1. Realised P/L ≤ ‑2 % equity intraday.  
2. Alpaca API latency > 3 s for > 30 consecutive calls.  
3. News classifier tags “black‑swan” (e.g. *earthquake*, *Fed surprise*) while positions open.

**Per‑trade limits**

| Rule | Value |
|------|-------|
| Position size cap | 2 % of equity |
| Hard stop‑loss | 1.5 × 5‑min ATR |
| Sector exposure cap | 6 % equity |

**Governance**

* All parameter changes require a dated entry in `model_change_log.md` and git tag.  
* Manual override via Telegram `/halt`—only owner may resume.  
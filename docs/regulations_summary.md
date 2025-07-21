# U.S. Securities & FINRA Rules — Day‑Trading / AI Governance  
_Last updated: {07/21/2025}_

## 1  FINRA Rule 4210 – Pattern‑Day‑Trader (PDT) Highlights
* **PDT trigger** – 4 or more round‑trip day trades in any five‑business‑day window **and** those trades exceed 6 % of total trades in the margin account.   
* **Equity floor** – Account must keep **≥ $25,000** (cash + margin‑eligible securities) **at all times** while day‑trading; if equity drops below, day‑trading is frozen until restored.   
* **Buying‑power cap** – Up to **4 ×** the account’s maintenance‑margin excess; exceeding it issues a day‑trading margin call (five business‑day cure). Unmet calls lock the account to 2 × power, then “cash only” for 90 days.   
* Rule 4210 cross‑references (¶ (f)(8)(B) et seq.) formalise the $25 k threshold and leverage limit inside FINRA’s margin framework. :contentReference[oaicite:15]{index=15}  

## 2  FINRA Investor Bulletin “Day Trading”
* Day trading **not permitted in cash accounts**; all purchases must settle before sale.   
* Firms may—and often do—impose stricter internal (“house”) equity requirements above FINRA’s minimum.   

## 3  SEC Regulation Best Interest (Reg BI) – Four Obligations
Applies to broker‑dealers making a “recommendation” to a retail customer (in any channel, including via AI model outputs).

| # | Obligation | Core Requirement |
|---|------------|------------------|
|1|**Disclosure**|Written disclosure of capacity, fees, scope of services & **all material conflicts** before or at the time of recommendation. :contentReference[oaicite:18]{index=18}|
|2|**Care**|Exercise reasonable diligence, care & skill to understand the product, consider reasonable alternatives, and ensure the recommendation is in the retail customer’s best interest. :contentReference[oaicite:19]{index=19}|
|3|**Conflict‑of‑Interest**|Maintain written policies to **identify, mitigate, or eliminate** conflicts (including those created by compensation, quotas, algorithms, etc.). :contentReference[oaicite:20]{index=20}|
|4|**Compliance**|Implement & test a supervisory system reasonably designed to achieve full Reg BI compliance. :contentReference[oaicite:21]{index=21}|

## 4  SEC July 2023 Proposed Rules – AI & Predictive Data Analytics Conflicts
* Would add **Exchange Act Rule 15l‑2** (broker‑dealers) & **Advisers Act Rule 211(h)(2)-4** (investment advisers). :contentReference[oaicite:22]{index=22}  
* **Covered technology** = any analytical/algorithmic process that “optimizes for, predicts, guides, forecasts, or directs investment‑related behaviours or outcomes.”  
* **Obligation** – Firms must **identify and _eliminate or neutralise_** any conflict where the tech puts the firm’s interest ahead of the investor’s.  
* **Governance** – Written policies must inventory models, testing, conflict reviews; annual effectiveness review required.  
* **Books & records** – Amendments to Rules 17a‑3/17a‑4 and 204‑2 require AI‑conflict artefacts to be retained **7 years (first 2 easily‑accessible)**, matching existing broker‑dealer/adviser retention cycles. :contentReference[oaicite:23]{index=23}  

## 5  Key Obligations Cheat‑Sheet
| Domain | What must the bot/team do? | Embedded Control (design hint) |
|--------|---------------------------|--------------------------------|
|**PDT rule**|Detect ≥ 4 round‑trips / 5 days; enforce $25 k equity; 4× leverage; 5‑day call → lock|Real‑time Alpaca equity & trade‑count check; automated kill‑switch|
|**Margin**|Apply FINRA Rule 4210 maintenance logic; auto‑halt if equity < req.|Risk engine module; nightly reconciliation|
|**Reg BI**|When algo issues a “recommendation,” log & attach disclosure; map to Care & Conflict controls|Model output filter; disclosure micro‑service|
|**AI Conflicts (proposed)**|Maintain inventory & testing docs; prove conflicts are eliminated/neutralised|Model‑governance pipeline w/ diff testing & audit store|
|**Record retention**|Keep all above artefacts **≥ 7 years** (2 yrs “live”)|AWS S3 `trade‑logs‑archive` bucket with Versioning + Object Lock|

---

### 6  Record‑Keeping Timeline Reference
| Rule Set | Retention Length | First 2 Years Readily Accessible? |
|----------|-----------------|------------------------------------|
|SEC 17a‑3 / 17a‑4 (BD) | 6 yrs (certain docs); 7 yrs post‑AI proposal | Yes |
|Advisers Act 204‑2 | 5 yrs; 7 yrs post‑AI proposal | Yes |

---

## 7  Practical Next Steps (feeds into Phase 1.2 risk & governance docs)
1. **Code PDT safeguards** – cron job/query Alpaca; block orders if threshold breached or equity < $25 k.  
2. **Draft Reg BI disclosure template** – include bot capacity, fee model, conflict statement.  
3. **Add “AI‑Conflict Assessment” section** to your `model_change_log.md`.  
4. **Configure S3 bucket** `trade-logs-archive` with object‑lock and 7‑year lifecycle policy.  
5. **Schedule annual policy review** (calendar‑based automation in GitHub Actions).

---

> _Prepared for Phase 1 completion. All citations link directly to authoritative rule text or SEC releases for easy drill‑down._
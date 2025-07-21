# Entity‑Selection Memo  
_Project: Self‑Driving Day‑Trading Bot_  
_Last updated: {{ today’s date }}_

| Structure | Liability Shield | Tax Filing & Treatment* | Typical Cost (set‑up / annual) | Compliance & Admin | Pros for Algo Trading | Cons / Risks |
|-----------|-----------------|-------------------------|-------------------------------|--------------------|----------------------|--------------|
| **Individual (Sole Prop)** | **None** – personal assets fully exposed to broker margin calls, model failures, or client disputes | Schedule C on Form 1040 (profits hit SE** tax) | $0 / $0 | Easiest: no separate EIN or state filings | • Zero cost • Simple bookkeeping | • Unlimited personal liability • Harder to open institutional brokerage & AWS accounts • Cannot bring in partners or investors |
| **Single‑Member LLC (default disregarded)** | **Strong** – member’s liability limited to capital in LLC (pierced only for fraud/commingling) | Still Schedule C passthrough; can elect S‑Corp later | \$50–\$200 state filing¹ / \$0–\$100 (biennial report) | EIN, separate bank, basic operating agreement | • Liability wall • Professional image (vendor NDAs, Alpaca API keys) • Business deductions for cloud, data feeds | • Minimal annual filing fees • Need separate books & bank account |
| **Multi‑Member LLC** | Strong (as above) | Form 1065 + K‑1s to members | \$100–\$200 / same | Operating agreement, partnership returns | • Easier to add co‑founders or investors | • Partnership tax complexity • Doesn’t fit a “solo” project today |
| **S‑Corp (LLC electing 2553)** | Strong | Form 1120‑S; wages + K‑1 for owner salary/distributions (FICA split) | marginal ↑ (payroll service) | Payroll tax filings, board minutes | • SE‑tax savings once net profit >≈ \$80‑100 k | • Not worth admin cost at launch; must run payroll |
| **C‑Corp** | Strong | Form 1120, double‑tax on dividends | \$100+ / \$50–\$500 | Full corporate formalities | • VC fund‑raising, QSBS | • Double taxation; far beyond current scope |

\* Assumes U.S. resident taxpayer.  
\** SE = Self‑Employment.

> ¹ State LLC fees vary. E.g. WY \$100, DE \$90, FL \$125, CA \$70 + $800 tax (waived first year).

---

### Regulatory & Brokerage Fit

* **FINRA PDT Rule (Rule 4210)** – broker must freeze day‑trading if equity < \$25 k; LLC shield prevents personal account sweep if algo misfires. :contentReference[oaicite:2]{index=2}  
* **Reg BI / AI‑Conflict logs** – easier to store audit artefacts under LLC’s S3 bucket and sign vendor DPA’s in entity name, isolating personal privacy.

---

## Decision

> **Based on the above, I will trade as a *single‑member LLC* because it gives me a clean liability firewall while keeping tax filing as simple as a sole proprietorship (Schedule C pass‑through). The one‑time state fee comfortably fits the \$50‑100 / mo ops budget, and the structure scales—if monthly profits ever justify payroll I can file an S‑Corp election without rewriting code or contracts.**

---

_Note: This memo is for planning purposes only and is **not** legal or tax advice. Confirm requirements in your state (or Wyoming/Delaware) and file Form SS‑4 for an EIN once the articles of organization are accepted._
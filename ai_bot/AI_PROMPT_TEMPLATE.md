## PROMPT

You are a quantitative swing-trade analyst.

Your task is to identify the **5 best stocks for a 5-day swing trade** (held Monday open → Friday close this week).

---

### RESEARCH PROCESS (work through each step before outputting)

All research should be valid and up to date.

**Step 1 — Macro context**
Briefly assess: current risk-on/risk-off tone, sector rotation signals, any major scheduled catalysts this week (Fed speakers, CPI, earnings).

**Step 2 — Candidate generation**
Generate a longlist of 10–15 candidates using at least three of the following lenses:
- Momentum: strong relative strength vs S&P 500 over past 10 days
- Catalyst: earnings beat, product launch, analyst upgrade, regulatory approval within last 5 days
- Technical setup: clear breakout above resistance, tight consolidation, high-volume accumulation
- Options flow: unusual call buying or elevated IV suggesting institutional positioning
- Sector theme: beneficiary of a current macro or geopolitical trend

**Step 3 — Shortlist to 5**
For each candidate, stress-test: What would make this trade fail? Eliminate stocks where the bear case dominates.

**Step 4 — Score each pick (0–100)**
Score each of your final 5 using this rubric:

| Dimension            | Max pts | Description                                                  |
|----------------------|---------|--------------------------------------------------------------|
| Momentum strength    | 20      | Relative strength vs benchmark, trend clarity                |
| Catalyst quality     | 20      | Specificity, timing, surprise factor                         |
| Technical setup      | 20      | Entry clarity, risk/reward ratio, volume confirmation        |
| Risk-adjusted return | 20      | Expected move vs likely drawdown over 5 days                 |
| Conviction / edge    | 20      | How differentiated is your view? Avoid consensus crowding    |

---

### OUTPUT FORMAT

After completing all research steps, output **only** the following block — no preamble, no explanation, no markdown outside this block.

Replace every [PLACEHOLDER] with real values. Do not omit any field.

```
===PICKS_START===
TICKER: [TICKER]
SCORE: [0-100]
EXCHANGE: [NYSE/NASDAQ/LSE/etc]
SECTOR: [sector name]
ENTRY: [price or "market open"]
STOP: [stop-loss price]
TARGET: [5-day price target]
CATALYST: [one sentence, max 15 words]
EDGE: [one sentence, max 15 words — what does the market not yet know?]

TICKER: [TICKER]
SCORE: [0-100]
EXCHANGE: [NYSE/NASDAQ/LSE/etc]
SECTOR: [sector name]
ENTRY: [price or "market open"]
STOP: [stop-loss price]
TARGET: [5-day price target]
CATALYST: [one sentence, max 15 words]
EDGE: [one sentence, max 15 words]

TICKER: [TICKER]
SCORE: [0-100]
EXCHANGE: [NYSE/NASDAQ/LSE/etc]
SECTOR: [sector name]
ENTRY: [price or "market open"]
STOP: [stop-loss price]
TARGET: [5-day price target]
CATALYST: [one sentence, max 15 words]
EDGE: [one sentence, max 15 words]

TICKER: [TICKER]
SCORE: [0-100]
EXCHANGE: [NYSE/NASDAQ/LSE/etc]
SECTOR: [sector name]
ENTRY: [price or "market open"]
STOP: [stop-loss price]
TARGET: [5-day price target]
CATALYST: [one sentence, max 15 words]
EDGE: [one sentence, max 15 words]

TICKER: [TICKER]
SCORE: [0-100]
EXCHANGE: [NYSE/NASDAQ/LSE/etc]
SECTOR: [sector name]
ENTRY: [price or "market open"]
STOP: [stop-loss price]
TARGET: [5-day price target]
CATALYST: [one sentence, max 15 words]
EDGE: [one sentence, max 15 words]
===PICKS_END===
```

---

### CONSTRAINTS

- All stocks must be listed on a recognised exchange (NYSE, NASDAQ, LSE, Euronext, etc.)
- All stocks must be accessible on Trading 212 (avoid OTC pink sheets, most ADRs are fine)
- No leveraged ETFs, inverse ETFs, or crypto-linked instruments
- Minimum market cap: $500M
- Minimum average daily volume: 500,000 shares
- Do not repeat a stock you picked last week (if applicable)
- Output the ===PICKS_START=== block only — no commentary before or after it

"""
Multi-AI Stock Trading Bot — Aggregator
========================================
Paste each AI's ===PICKS_START=== ... ===PICKS_END=== block into the
AI_RESPONSES dict below, then run:  python aggregator.py

Rules:
  - Only stocks recommended by >= MIN_CONSENSUS AIs are considered
  - Ranked by average score (highest first) among recommending AIs
  - Top 5 selected; capital allocated proportionally to average score
"""

import re
from collections import defaultdict

# ─── CONFIG ──────────────────────────────────────────────────────────────────

MIN_CONSENSUS = 2          # minimum number of AIs that must pick a stock
TOP_N         = 5          # number of stocks to allocate capital across
TOTAL_CAPITAL = 10_000     # £ / $ — used only for illustrative £ allocation

# ─── PASTE AI RESPONSES HERE ─────────────────────────────────────────────────
# Replace the empty strings with each AI's full output block.
# The parser only reads between ===PICKS_START=== and ===PICKS_END===.

AI_RESPONSES = {
    "Gemini": """
===PICKS_START===
TICKER: AMD
SCORE: 85
EXCHANGE: NASDAQ
SECTOR: Semiconductors
ENTRY: market open
STOP: 162.50
TARGET: 178.00
CATALYST: Expected server CPU market share gain report.
EDGE: Supply chain checks indicate higher than expected Q2 yields.

TICKER: CRWD
SCORE: 92
EXCHANGE: NASDAQ
SECTOR: Cybersecurity
ENTRY: market open
STOP: 310.00
TARGET: 335.00
CATALYST: New zero-trust module launch next Wednesday.
EDGE: Competitor breaches driving immediate emergency enterprise deployments.

TICKER: PLTR
SCORE: 88
EXCHANGE: NYSE
SECTOR: Software
ENTRY: market open
STOP: 22.50
TARGET: 26.50
CATALYST: Unannounced DOD contract extension expected this week.
EDGE: Unusually aggressive near-term call buying signals institutional confidence.

TICKER: UBER
SCORE: 81
EXCHANGE: NYSE
SECTOR: Transportation
ENTRY: market open
STOP: 75.00
TARGET: 84.00
CATALYST: Analyst day highlighting autonomous delivery margins.
EDGE: Market underestimating the take-rate expansion in suburban markets.

TICKER: HOOD
SCORE: 79
EXCHANGE: NASDAQ
SECTOR: Financial Services
ENTRY: market open
STOP: 18.20
TARGET: 21.50
CATALYST: Rollout of new high-yield cash sweep features.
EDGE: Retail deposit inflows are accelerating faster than consensus estimates.
===PICKS_END===
""",

    "Claude": """
===PICKS_START===
TICKER: MU
SCORE: 87
EXCHANGE: NASDAQ
SECTOR: Semiconductors
ENTRY: market open
STOP: 400.00
TARGET: 455.00
CATALYST: HBM4 sold out through 2027; Q3 guidance doubled Street consensus in March blowout.
EDGE: Market underestimates that helium supply (critical for chip fab) normalises with Hormuz reopening.

TICKER: META
SCORE: 84
EXCHANGE: NASDAQ
SECTOR: Technology / Social Media
ENTRY: market open
STOP: 610.00
TARGET: 665.00
CATALYST: Muse Spark AI model launch plus $21B CoreWeave deal driving pre-earnings momentum into April 29.
EDGE: Stock trades at 18x forward PE — near 3-year trough multiple — despite 33% YoY revenue growth outlook.

TICKER: AVGO
SCORE: 82
EXCHANGE: NASDAQ
SECTOR: Semiconductors
ENTRY: market open
STOP: 352.00
TARGET: 400.00
CATALYST: New Google and Anthropic custom TPU deal announced; AI revenue up 106% YoY in Q1 2026.
EDGE: Analyst 12-month consensus target $435 implies 17% upside; Zacks Rank #1 Strong Buy rarely maintained at this AI revenue run rate.

TICKER: RCL
SCORE: 76
EXCHANGE: NYSE
SECTOR: Consumer Discretionary / Cruise
ENTRY: market open
STOP: 262.00
TARGET: 300.00
CATALYST: Ceasefire-driven oil decline directly reduces fuel costs; 85% of 2026 capacity booked at record pricing.
EDGE: RCL's private-destination strategy (Perfect Day at CocoCay) insulates yield from Middle East sentiment, unlike peers — market has not priced this premium.

TICKER: UAL
SCORE: 73
EXCHANGE: NASDAQ
SECTOR: Airlines
ENTRY: market open
STOP: 90.00
TARGET: 108.00
CATALYST: Steep jet fuel cost decline post-ceasefire; Q1 2026 earnings April 22 with 24.2% YoY EPS growth anticipated.
EDGE: Premium cabin revenue growing 14x faster than main cabin — margin quality exceeds what depressed stock price implies.
===PICKS_END===
""",

    "ChatGPT": """
===PICKS_START===
TICKER: NVDA
SCORE: 91
EXCHANGE: NASDAQ
SECTOR: Semiconductors
ENTRY: market open
STOP: 830
TARGET: 910
CATALYST: Continued AI demand momentum and strong institutional inflows
EDGE: Market underpricing near-term upside from hyperscaler capex acceleration

TICKER: AMD
SCORE: 88
EXCHANGE: NASDAQ
SECTOR: Semiconductors
ENTRY: market open
STOP: 158
TARGET: 178
CATALYST: Positive AI chip sentiment spillover and recent analyst upgrades
EDGE: MI300 adoption curve underestimated versus NVDA dominance narrative

TICKER: TSLA
SCORE: 85
EXCHANGE: NASDAQ
SECTOR: Consumer Discretionary
ENTRY: market open
STOP: 160
TARGET: 185
CATALYST: Short-term rebound after oversold conditions and high retail inflows
EDGE: Positioning extremely bearish, creating squeeze potential

TICKER: SMCI
SCORE: 89
EXCHANGE: NASDAQ
SECTOR: Information Technology
ENTRY: market open
STOP: 880
TARGET: 1020
CATALYST: AI server demand strength and continued momentum breakout
EDGE: Underestimated operating leverage from AI infrastructure scaling

TICKER: COIN
SCORE: 84
EXCHANGE: NASDAQ
SECTOR: Financials
ENTRY: market open
STOP: 210
TARGET: 255
CATALYST: Bitcoin strength driving volume and revenue expectations higher
EDGE: Options flow signaling institutional upside positioning
===PICKS_END===
""",

    "Grok": """
===PICKS_START===
TICKER: JPM
SCORE: 93
EXCHANGE: NYSE
SECTOR: Financial Services
ENTRY: market open
STOP: 295.00
TARGET: 325.00
CATALYST: Q1 earnings Tuesday with expected beat
EDGE: Financial rotation strength not yet in consensus pricing

TICKER: MS
SCORE: 91
EXCHANGE: NYSE
SECTOR: Financial Services
ENTRY: market open
STOP: 169.00
TARGET: 190.00
CATALYST: Q1 earnings Wednesday robust trading
EDGE: Pre-earnings accumulation signals hidden institutional edge

TICKER: C
SCORE: 88
EXCHANGE: NYSE
SECTOR: Financial Services
ENTRY: market open
STOP: 118.00
TARGET: 135.00
CATALYST: Q1 earnings this week sector tailwind
EDGE: Net interest margin surprise ahead of Fed speakers

TICKER: TSM
SCORE: 86
EXCHANGE: NYSE
SECTOR: Technology
ENTRY: market open
STOP: 355.00
TARGET: 395.00
CATALYST: Q1 earnings Thursday AI demand beat
EDGE: 3nm capacity tightness underestimated by market

TICKER: INTC
SCORE: 84
EXCHANGE: NASDAQ
SECTOR: Technology
ENTRY: market open
STOP: 58.00
TARGET: 70.00
CATALYST: Breakout above resistance high volume
EDGE: Value semi rotation accelerating beyond tech selloff
===PICKS_END===
""",

    "DeepSeek": """
===PICKS_START===
TICKER: NVDA
SCORE: 92
EXCHANGE: NASDAQ
SECTOR: Technology
ENTRY: market open
STOP: 180.00
TARGET: 210.00
CATALYST: 7-day win streak, bullish options flow, AI chip demand.
EDGE: Options OI walls at 180-190 signal strong institutional positioning.

TICKER: SMCI
SCORE: 88
EXCHANGE: NASDAQ
SECTOR: Technology
ENTRY: market open
STOP: 22.00
TARGET: 32.00
CATALYST: +8.79% breakout on heavy volume, AI infrastructure momentum.
EDGE: Market underestimates earnings leverage from NVIDIA server ramp.

TICKER: COHR
SCORE: 85
EXCHANGE: NYSE
SECTOR: Technology
ENTRY: market open
STOP: 280.00
TARGET: 350.00
CATALYST: 8.2% surge on optical networking demand, AI data center buildout.
EDGE: Valuation disconnect as optical component cycle accelerates.

TICKER: AVGO
SCORE: 83
EXCHANGE: NASDAQ
SECTOR: Technology
ENTRY: market open
STOP: 350.00
TARGET: 420.00
CATALYST: 4.7% gain with $48B volume, custom AI chip momentum.
EDGE: AI ASIC ramp ahead of Q2 earnings not fully priced in.

TICKER: NFLX
SCORE: 80
EXCHANGE: NASDAQ
SECTOR: Communication Services
ENTRY: market open
STOP: 98.00
TARGET: 115.00
CATALYST: Q1 earnings April 16 with 15% revenue growth expected.
EDGE: Recent price hikes and ad-tier adoption support margin upside.
===PICKS_END===
"""
}

# ─── PARSER ──────────────────────────────────────────────────────────────────

def parse_picks(name: str, raw: str) -> list[dict]:
    """Extract structured picks from a single AI's output block."""
    block_match = re.search(
        r"===PICKS_START===(.*?)===PICKS_END===", raw, re.DOTALL
    )
    if not block_match:
        print(f"  [WARN] No valid picks block found for {name}")
        return []

    block = block_match.group(1).strip()
    picks = []

    # Split on blank lines between picks
    entries = re.split(r"\n{2,}", block)
    for entry in entries:
        entry = entry.strip()
        if not entry:
            continue

        fields = {}
        for line in entry.splitlines():
            if ":" in line:
                key, _, val = line.partition(":")
                fields[key.strip().upper()] = val.strip()

        ticker = fields.get("TICKER", "").upper()
        score_raw = fields.get("SCORE", "")

        if not ticker:
            continue

        try:
            score = float(re.sub(r"[^\d.]", "", score_raw))
        except (ValueError, TypeError):
            print(f"  [WARN] Could not parse score for {ticker} from {name}: '{score_raw}'")
            continue

        picks.append({
            "ticker":   ticker,
            "score":    score,
            "exchange": fields.get("EXCHANGE", "—"),
            "sector":   fields.get("SECTOR",   "—"),
            "entry":    fields.get("ENTRY",     "—"),
            "stop":     fields.get("STOP",      "—"),
            "target":   fields.get("TARGET",    "—"),
            "catalyst": fields.get("CATALYST",  "—"),
            "edge":     fields.get("EDGE",      "—"),
            "source":   name,
        })

    return picks

# ─── AGGREGATION ─────────────────────────────────────────────────────────────

def aggregate(responses: dict, min_consensus: int) -> list[dict]:
    """
    For each ticker: collect all scores, filter by min_consensus,
    compute average, return sorted list.
    """
    data: dict[str, dict] = defaultdict(lambda: {"scores": [], "meta": {}})

    for ai_name, raw in responses.items():
        picks = parse_picks(ai_name, raw)
        for p in picks:
            t = p["ticker"]
            data[t]["scores"].append((ai_name, p["score"]))
            # Store metadata from the highest-scoring source
            if not data[t]["meta"] or p["score"] > data[t]["meta"].get("score", -1):
                data[t]["meta"] = p

    results = []
    for ticker, info in data.items():
        n = len(info["scores"])
        if n < min_consensus:
            continue
        avg = sum(s for _, s in info["scores"]) / n
        sources = [ai for ai, _ in info["scores"]]
        results.append({
            "ticker":   ticker,
            "avg_score": round(avg, 1),
            "count":    n,
            "sources":  sources,
            "meta":     info["meta"],
        })

    results.sort(key=lambda x: x["avg_score"], reverse=True)
    return results

# ─── ALLOCATION ──────────────────────────────────────────────────────────────

def allocate(ranked: list[dict], top_n: int, capital: float) -> list[dict]:
    """Proportional allocation based on average score."""
    top = ranked[:top_n]
    total_score = sum(s["avg_score"] for s in top)
    for s in top:
        s["alloc_pct"] = round(s["avg_score"] / total_score * 100, 1)
        s["alloc_gbp"] = round(s["avg_score"] / total_score * capital, 2)
    return top

# ─── OUTPUT ──────────────────────────────────────────────────────────────────

def print_summary(top: list[dict], capital: float):
    sep = "─" * 68

    print(f"\n{'MULTI-AI SWING TRADE — WEEKLY PICKS':^68}")
    print(sep)
    print(f"{'Stock':<8} {'Avg Score':>10} {'AIs':>4} {'Alloc %':>9} {'Alloc £':>10}  {'Exchange'}")
    print(sep)
    for s in top:
        print(
            f"{s['ticker']:<8} "
            f"{s['avg_score']:>10.1f} "
            f"{s['count']:>4} "
            f"{s['alloc_pct']:>8.1f}% "
            f"{s['alloc_gbp']:>10,.2f}  "
            f"{s['meta']['exchange']}"
        )
    print(sep)

    print(f"\n{'DETAIL':^68}")
    print(sep)
    for s in top:
        m = s["meta"]
        print(f"\n  {s['ticker']}  |  Avg {s['avg_score']}  |  {', '.join(s['sources'])}")
        print(f"  Entry: {m['entry']}   Stop: {m['stop']}   Target: {m['target']}")
        print(f"  Catalyst: {m['catalyst']}")
        print(f"  Edge:     {m['edge']}")

    print(f"\n{sep}")
    print(f"  Total capital: £{capital:,.0f}   Consensus threshold: ≥{MIN_CONSENSUS} AIs   Top {TOP_N} selected")
    print(sep)


def print_rejected(ranked: list[dict], top_n: int):
    """Show stocks that made consensus but didn't crack the top N."""
    rest = ranked[top_n:]
    if not rest:
        return
    print(f"\n  Consensus but not selected (rank {top_n + 1}+):")
    for s in rest:
        print(f"    {s['ticker']}  avg {s['avg_score']}  ({s['count']} AIs)")


# ─── MAIN ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\nParsing AI responses...")
    all_ranked = aggregate(AI_RESPONSES, MIN_CONSENSUS)

    if not all_ranked:
        print(
            f"\n  No stocks reached the ≥{MIN_CONSENSUS}-AI consensus threshold.\n"
            "  Check that each AI block is correctly pasted and delimited."
        )
    else:
        top = allocate(all_ranked, TOP_N, TOTAL_CAPITAL)
        print_summary(top, TOTAL_CAPITAL)
        print_rejected(all_ranked, TOP_N)

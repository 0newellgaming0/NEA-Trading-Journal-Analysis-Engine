# =========================================================
# RELATIVE STRENGTH ENGINE (BLOCK-BASED INTEGRATION MODULE)
# FIXED + EXPANDED INSTITUTIONAL PROMPT LAYER RESTORED
# =========================================================

import pandas as pd
import numpy as np
import os

from modules.ohlcv_normalizer import normalize_timestamp


# =========================================================
# BENCHMARK STRUCTURE
# =========================================================

BENCHMARK_GROUPS = {
    "mega_cap": ["SPY", "QQQ", "DIA"],
    "growth": ["QQQ", "VUG"],
    "broad_market": ["SPY", "VTI"],
    "small_cap": ["IWM", "IJR"]
}


# =========================================================
# PATH RESOLUTION
# =========================================================

def get_stock_data_path(ticker, timeframe="daily"):
    return os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "stock_data",
        timeframe,
        f"{ticker}.csv"
    )


# =========================================================
# DATA LOADER
# =========================================================

def load_history(ticker, timeframe="daily"):
    path = get_stock_data_path(ticker, timeframe)

    if not os.path.exists(path):
        return None

    try:
        return pd.read_csv(path)
    except Exception:
        return None


# =========================================================
# COLUMN RESOLUTION
# =========================================================

def get_close_column(df, ticker):

    if df is None:
        return None

    t = ticker.lower()
    col = f"close_{t}"

    if col in df.columns:
        return col

    return None


# =========================================================
# CORE RS CALCULATION
# =========================================================

def compute_rs(asset_df, bench_df, ticker, bench_ticker):

    asset_col = get_close_column(asset_df, ticker)
    bench_col = get_close_column(bench_df, bench_ticker)

    if asset_col is None or bench_col is None:
        return None

    df = pd.DataFrame({
        "asset": pd.to_numeric(asset_df[asset_col], errors="coerce"),
        "bench": pd.to_numeric(bench_df[bench_col], errors="coerce")
    })

    df = df.dropna()

    if len(df) < 20:
        return None

    rs = df["asset"] / df["bench"]

    return {
        "latest": float(rs.iloc[-1]),
        "trend": float(rs.iloc[-1] - rs.iloc[-10])
    }


# =========================================================
# BENCHMARK CLASSIFICATION
# =========================================================

def classify_benchmark(bm):
    for group, items in BENCHMARK_GROUPS.items():
        if bm in items:
            return group
    return "unknown"


# =========================================================
# CORE ENGINE
# =========================================================

def build_relative_strength_block(ticker, timeframe="daily"):

    asset = load_history(ticker, timeframe)

    if asset is None:
        return f"""
===========================
📊 RELATIVE STRENGTH CONTEXT
===========================

❌ STATUS:
No asset data found for {ticker}

Expected:
→ {get_stock_data_path(ticker, timeframe)}
"""

    results = []

    for group, benchmarks in BENCHMARK_GROUPS.items():
        for bm in benchmarks:

            bench = load_history(bm, timeframe)
            if bench is None:
                continue

            rs = compute_rs(asset, bench, ticker, bm)
            if rs is None:
                continue

            results.append({
                "bm": bm,
                "group": group,
                "latest": rs["latest"],
                "trend": rs["trend"]
            })

    if not results:
        return f"""
===========================
📊 RELATIVE STRENGTH CONTEXT
===========================

Ticker: {ticker}

⚠️ STATUS:
No benchmark data available

→ Check CSV structure
→ Ensure close_{ticker} format exists
→ Ensure normalization alignment
"""

    # =====================================================
    # STRUCTURAL METRICS
    # =====================================================

    avg_rs = sum(r["latest"] for r in results) / len(results)

    strongest = max(results, key=lambda x: x["latest"])
    weakest = min(results, key=lambda x: x["latest"])

    improving = sum(1 for r in results if r["trend"] > 0)
    weakening = sum(1 for r in results if r["trend"] < 0)

    regime = (
        "Leadership → Outperforming benchmark basket" if avg_rs > 1.05
        else "Neutral → Tracking benchmarks" if avg_rs > 0.98
        else "Lagging → Underperforming benchmark basket"
    )

    flow = (
        "Positive rotation bias" if improving > weakening
        else "Negative rotation bias" if weakening > improving
        else "Balanced / rotational equilibrium"
    )


    # =====================================================
    # EXPANDED INSTITUTIONAL INTERPRETATION LAYER (RESTORED + EXTENDED)
    # =====================================================

    interpretation = f"""

===========================
📊 INSTITUTIONAL RELATIVE STRENGTH ANALYSIS
===========================

Ticker: {ticker}
Timeframe: {timeframe}

📊 STRUCTURAL OVERVIEW

{ticker} is currently positioned in a:
→ {regime}

This classification is derived from comparative performance against major liquidity benchmarks including mega-cap, growth, and broad-market indices.

The current average relative strength reading of {avg_rs:.4f} indicates:

→ Relative participation in index-wide expansion is {'strong' if avg_rs > 1.05 else 'moderate' if avg_rs > 0.98 else 'weak'}
→ Institutional capital flow alignment is {'positive' if improving > weakening else 'negative'}
→ Beta transmission into risk-on environments is {'elevated' if avg_rs > 1.0 else 'suppressed'}

----------------------------------------------------

🏆 BENCHMARK LEADERSHIP STRUCTURE

Strongest Relative Benchmark:
→ {strongest['bm']} ({classify_benchmark(strongest['bm'])})
RS: {strongest['latest']:.4f}

Interpretation:
→ Relative strength peak concentration area
→ Indicates where asset responds most effectively to benchmark expansion regimes
→ Useful for identifying rotational sensitivity clusters

Weakest Relative Benchmark:
→ {weakest['bm']} ({classify_benchmark(weakest['bm'])})
RS: {weakest['latest']:.4f}

Interpretation:
→ Relative weakness concentration zone
→ Highlights structural drag in comparative performance
→ Useful for identifying capital rotation outflow zones

----------------------------------------------------

📈 ROTATION STRUCTURE ANALYSIS

Improving vs benchmarks: {improving}
Weakening vs benchmarks: {weakening}

Interpretation:

- Improving dominance:
  → Stabilization or early recovery behavior
  → Relative selling pressure reduction
  → Potential transition from lagging → neutral regime

- Weakening dominance:
  → Relative underperformance persistence
  → Momentum continuation in benchmark outperformance
  → Rotation away from asset exposure

Current Flow State:
→ {flow}

----------------------------------------------------

📊 FLOW DYNAMICS (INSTITUTIONAL CONTEXT)

Flow Bias: {flow}

Key Insight:

→ Positive rotation bias reflects deceleration in relative underperformance, NOT outright strength
→ Regime change requires sustained RS expansion above benchmark cluster
→ Flow should be interpreted as comparative trend velocity, not directional certainty

----------------------------------------------------

📌 FINAL INSTITUTIONAL SUMMARY

{ticker} is currently characterized as:

→ {'a leadership candidate' if avg_rs > 1.05 else 'a neutral rotation candidate' if avg_rs > 0.98 else 'a lagging liquidity participant'}
→ {'structurally aligned with risk-on regimes' if avg_rs > 1.0 else 'structurally lagging macro index expansion'}
→ {'showing accumulation behavior' if improving > weakening else 'showing relative distribution pressure'}

Institutional implication:

→ System reflects RELATIVE positioning only (not absolute price strength)
→ Best used for rotation detection and benchmark sensitivity mapping
→ Requires multi-period confirmation before regime transition validation
→ Should not be interpreted as standalone directional prediction model

===========================
"""

    return interpretation
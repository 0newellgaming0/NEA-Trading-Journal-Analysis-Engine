# prompt_engine.py

from datetime import datetime


def generate_signal_template(
    row,
    load_market_context,
    load_intraday_15m,
    load_intraday_60m,
    load_weekly,
    format_financial_prompt,
    load_yahoo_history,
    load_volume_analysis,
    analyze_tline_intraday,
    analyze_dual_timeframe_momentum,
    analyze_multitimeframe_candlesticks,
    format_candlestick_for_journal,
    run_liquidity_multi_timeframe_engine,
    run_wyckoff_pnf_analysis,
    format_pnf_for_journal,
    analyze_pinbar,
    analyze_wyckoff_fractals,
    format_fractal_for_journal,
    yf,
    analyze_historical_data
):

    ticker = row.get("ticker", "").upper()

    daily_df, intraday_df, weekly_df = load_market_context(ticker)

    intraday_15m_df = load_intraday_15m(ticker)
    intraday_60m_df = load_intraday_60m(ticker)

    financial_block = "[FUNDAMENTALS]\n" + format_financial_prompt(ticker)

    history_block = load_yahoo_history(ticker, "daily", 80)
    weekly_block = load_yahoo_history(ticker, "weekly", 80)

    daily_volume_block = load_volume_analysis(ticker, "daily", 80)
    intraday_block = load_yahoo_history(ticker, "intraday_60m", 40)
    volume_block = load_volume_analysis(ticker, "intraday_60m", 40)

    intraday_15m_prompt = analyze_tline_intraday(intraday_15m_df, ticker, "15M")
    intraday_60m_prompt = analyze_tline_intraday(intraday_60m_df, ticker, "60M")

    dtfm_prompt = analyze_dual_timeframe_momentum(
        intraday_60m_df,
        daily_df,
        ticker,
        "DTFM"
    )

    try:
        candlestick_result = analyze_multitimeframe_candlesticks(
            intraday_15m_df,
            intraday_60m_df,
            daily_df,
            ticker
        )
        candlestick_block = format_candlestick_for_journal(candlestick_result)
    except Exception as e:
        candlestick_block = f"Candlestick analysis unavailable: {e}"

    try:
        liquidity_output = run_liquidity_multi_timeframe_engine({
            "15m": intraday_15m_df,
            "60m": intraday_60m_df,
            "1D": daily_df,
            "weekly": weekly_df
        })

        phase_context_block = liquidity_output.get("phase_context_block", "")
        liquidity_block = liquidity_output.get("liquidity_block", "")

    except Exception as e:
        phase_context_block = f"Liquidity error: {e}"
        liquidity_block = f"Liquidity error: {e}"

    try:
        pnf_result = run_wyckoff_pnf_analysis(
            ticker=ticker,
            timeframe="daily",
            box_size=1.0,
            reversal=3
        )
        pnf_block = format_pnf_for_journal(pnf_result)
    except Exception as e:
        pnf_block = f"PnF error: {e}"

    pinbar_result = analyze_pinbar(daily_df)
    pinbar_block = pinbar_result.get("journal_prompt", "")

    try:
        fractal_result = analyze_wyckoff_fractals(daily_df, ticker=ticker)
        fractal_block = format_fractal_for_journal(fractal_result)
    except Exception as e:
        fractal_block = f"Fractal error: {e}"

    try:
        historical_df = yf.download(
            ticker,
            period="5y",
            interval="1d",
            auto_adjust=True,
            progress=False
        )

        historical_analysis = analyze_historical_data(historical_df, ticker=ticker)

        historical_results = historical_analysis.get("prompt_summary", "")

    except Exception as e:
        historical_results = f"Historical error: {e}"

    try:
        buy_now = float(row.get("buy_now_price", 0))
        stop_val = float(row.get("stop", 0))
        rr_target_val = buy_now + 2 * (buy_now - stop_val)
    except:
        rr_target_val = ""

    template = f"""
    ==================================================
    POTENTIAL SINGLE ENTRY
    ==================================================

    Evaluate whether {row.get("buy_now_price","")} represents a valid entry point using information now available, and determine whether that entry location aligns with institutional structure, along with a stop loss at {row.get("stop","")}. 

    Account Size: {row.get("account","")}
    Risk Dollar: {row.get("risk_dollar","")}

    Journal Entry Shares: {row.get("buy_now_shares","")}
    Journal Entry Total: {row.get("buy_now_total","")}

    ==================================================
    POTENTIAL DOUBLE ENTRY
    ==================================================
    
    Range High Price: {row.get("ladder_1_price","")}
    Shares: {row.get("ladder_1_shares","")}
    Trade Total: {row.get("ladder_1_total","")}

    Range Low Price: {row.get("ladder_2_price","")}
    Shares: {row.get("ladder_2_shares","")}
    Trade Total: {row.get("ladder_2_total","")}  
    
    ==================================================
 
    
📅Today's Date: {datetime.now().isoformat()}
📅Journal Entry Date: {row.get('timestamp','').split('T')[0]}
📈Ticker: {row.get('ticker','')}

{stop_block}
{candlestick_block}
{pinbar_block}
{financial_block}
{historical_results}
{intraday_60m_prompt }
{intraday_15m_prompt }
{weekly_block}
{history_block}
{daily_volume_block}
{intraday_block}
{volume_block}
{dtfm_prompt}
{pnf_block}
{fractal_block}
{phase_context_block}
{liquidity_block}
{rs_block}

Include detailed tline information targeted toward the possibility of j hook continuations and/or other tline specific patterns.
Analyze momentum indicators in context with short term daily trend direction.

📊 Under/Overvalue Determination
📈 Earnings Growth Rate (Aggressive, Moderate, Passive)

📌 Conduct a thorough William O'Neal Analysis (Do a true institutional-grade O’Neil teardown:
✅ {row.get('ticker','')} Current Exact Quarterly Earnings/Share vs Previous Exact Quarterly Earnings/Share % Change - +40% or more is GREAT!
✅ {row.get('ticker','')} Consensus Earnings Estimates Next few Quarters/Next 2 Years, if available
✅ {row.get('ticker','')} Annual Earnings Increases over last 3 years +25%, 50% or more is GREAT!
✅ {row.get('ticker','')} Annual Cash Flow/Share > Annual Earnings/Share +20% or more is GREAT!
✅ {row.get('ticker','')} Earnings Stability Numbers
✅ New Management/Products/Services, etc.(Earnings Catalysts)
✅ Supply/Demand - Share Outstanding + Big Volume Demand
✅ Leader or Lagger
✅ Institutional Sponsorship - 12 Month Quality Check - Public institutional ownership (13F summaries where visible, 1+ important) 
--Analyze sponsorship quality - validate sponsors past 36 month performance
--Increasing sponsorship over past quarters
✅ Market Direction

🧠 Institutional Rationale Summary

1) Strategic Entry Setup — Deep Value + Structural Support
- Entry confirmation based on technical/fundamental triggers
- Stop-loss levels and risk tolerance
- Position sizing based on risk per trade
- Reward-to-risk ratio verification
- Profit-taking levels and scaling strategy
- Scenario analysis: best-case, base-case, worst-case
- Contingency plan for trade failure

2) Fundamental Catalysts
- Income statement trends: revenue, net income, EPS
- Balance sheet overview: assets, liabilities, equity, debt ratios
- Cash flow analysis: operating and free cash flow, capital expenditures
- Key ratios: ROE, ROA, gross margin, net margin, P/E, PEG, P/B, EV/EBITDA, current ratio, debt/equity, asset turnover
- Historical and forecasted growth rates
- Management quality and track record
- Competitive advantages and market positioning
- Regulatory, legal, or macroeconomic risks
- Strategic initiatives: M&A, partnerships, product launches

3) Macro & Competitive Tailwinds
- Recent news, press releases, earnings reports
- Insider and institutional buying/selling activity
- Analyst ratings, upgrades/downgrades, and price targets
- Sector and macroeconomic trends impacting the stock
- Social media and forum sentiment analysis
- Options market activity and unusual volume

4) Risk Considerations (Validated by Street Commentary)
🧩 Technical & Behavioral Context
- Identify long-term, medium-term, and short-term trends
- Key support and resistance levels
- Trendlines, channels, and Fibonacci retracement levels
- Chart patterns: head & shoulders, triangles, double/triple tops/bottoms
- Wyckoff phases: accumulation, distribution, markup, markdown
- Candlestick pattern recognition
- Indicators: SMA, EMA, MACD, RSI, Stochastic, ADX
- Volume analysis: OBV, accumulation/distribution, volume spikes
- Volatility measures: ATR, beta, implied volatility

🟧 Supply & Demand Zone Mapping

✅ Trade Logic, Stop Management & Thesis
- Document rationale for entry and exit
- Use relevant ticker ATR combined with float size, relative volume, volatility regime, short interest, and catalyst classification to assess and analyze stop placement. 
- Assess correctness of technical/fundamental assumptions
- Adjust future trade strategy based on information attained
- Explain adjustments suggestions in detail and reasoning.

🌳 Scenario Tree (Probability‑Weighted)

⚖️ Risk vs Opportunity Assessment

===========================

📌 Advanced Analysis
- Multi-timeframe Wyckoff or Elliott Wave overlays
- Correlation vs sector/index ETFs
- Algorithmic scoring or ranking
- Monte Carlo simulations for probability-weighted outcomes
- Wyckoff Cause and Effect PnF Analysis
- Fractal Analysis (Breakouts, Breakdowns)

===========================

📊 Summary View

📌 Investment Takeaway

Output:
--------
- Provide a structured report suitable for dashboard panels
- Include charts, calculations, and textual analysis where applicable
- Highlight key trade signals, risk/reward, and actionable insights
- Create a visual image flyer displaying this information. do not include the following in the visual flyer : point and figure chart, no charts for momentum, only data display, no share amounts for trade should be included, only entry, stop placements and risk allocation percentage.
"""

    return template
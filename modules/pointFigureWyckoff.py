import numpy as np
import pandas as pd
from datetime import datetime
import os


# =========================================================
# SAFE HELPERS
# =========================================================

def safe_float(x):
    try:
        return float(x)
    except:
        return 0.0


def poly_slope(arr):
    try:
        if arr is None or len(arr) < 2:
            return 0.0

        arr = np.asarray(arr, dtype=float)
        arr = arr[~np.isnan(arr)]

        if len(arr) < 2:
            return 0.0

        x = np.arange(len(arr))
        return np.polyfit(x, arr, 1)[0]

    except:
        return 0.0

# =========================================================
# PROJECT ROOT RESOLUTION
# =========================================================

def get_project_root():
    current = os.path.dirname(os.path.abspath(__file__))
    while current != os.path.dirname(current):
        if os.path.exists(os.path.join(current, "modules")):
            return current
        current = os.path.dirname(current)
    return os.path.dirname(os.path.abspath(__file__))


def get_stock_data_path(ticker, timeframe):
    return os.path.join(
        get_project_root(),
        "modules",
        "stock_data",
        timeframe,
        f"{ticker}.csv"
    )


# =========================================================
# SCHEMA NORMALIZATION
# =========================================================

def normalize_ohlcv_columns(df, ticker):
    t = ticker.lower()

    mapping = {
        f"open_{t}": "Open",
        f"high_{t}": "High",
        f"low_{t}": "Low",
        f"close_{t}": "Close",
        f"volume_{t}": "Volume",
        f"adj_close_{t}": "Adj Close"
    }

    for old, new in mapping.items():
        if old in df.columns and new not in df.columns:
            df[new] = df[old]

    return df


# =========================================================
# DATA LOADING
# =========================================================

def load_data(ticker, timeframe, limit=300):

    path = get_stock_data_path(ticker, timeframe)

    if not os.path.exists(path):
        return None

    df = pd.read_csv(path)

    if df is None or df.empty:
        return None

    df = df.tail(limit).copy()
    df = normalize_ohlcv_columns(df, ticker)

    required = ["High", "Low", "Close", "Volume"]

    for c in required:
        if c not in df.columns:
            return None
        df[c] = pd.to_numeric(df[c], errors="coerce")

    df = df.dropna(subset=required)

    if len(df) < 20:
        return None

    return df


# =========================================================
# MULTI-TIMEFRAME LOADING
# =========================================================

TIMEFRAMES = {
    "intraday": "intraday_60m",
    "daily": "daily",
    "weekly": "weekly"
}


def load_multi_timeframe(ticker):
    out = {}

    for key, tf in TIMEFRAMES.items():
        df = load_data(ticker, tf)
        if df is not None and len(df) > 0:
            out[key] = df

    return out
    
# =========================================================
# ANALYZE VOLUME
# =========================================================

def analyze_volume(df):

    vol = df["Volume"].values

    if len(vol) < 5:
        return {
            "state": "UNKNOWN",
            "trend": 0.0,
            "relative_last": 0.0
        }

    vol_mean = np.mean(vol)
    vol_std = np.std(vol)

    if vol_std == 0:
        vol_std = 1e-9

    trend = poly_slope(vol)

    relative_last = vol[-1] / vol_mean if vol_mean else 0

    if relative_last > 1.5:
        state = "EXPANDING"
    elif relative_last < 0.7:
        state = "CONTRACTING"
    else:
        state = "NORMAL"

    return {
        "state": state,
        "trend": trend,
        "relative_last": relative_last
    }
    
# =========================================================
# VOLUME CONFIRMATION FOR P&F BREAKOUTS
# =========================================================
def is_volume_confirmed_breakout(cols, df, lookback=20):
    if not cols or df is None or len(df) < lookback:
        return False

    vol = df["Volume"].values

    last_dir, last_col = cols[-1]

    if not last_col:
        return False

    avg_vol = np.mean(vol[-lookback:])
    if avg_vol == 0:
        return False

    last_vol = vol[-1]
    vol_ratio = last_vol / avg_vol

    # confirm only meaningful expansion
    return vol_ratio >= 1.25
    
# =========================================================
# COMPUTE HORIZONTAL COUNT
# =========================================================

def compute_horizontal_count(cols, box_size, reversal=3):

    if not cols or len(cols) < 3:
        return 0.0

    congestion_width = 0

    for item in reversed(cols):

        if not item or len(item) != 2:
            continue

        direction, column = item

        if not column or len(column) < reversal:
            break

        congestion_width += 1

        if congestion_width >= 5:
            break

    return congestion_width * box_size * reversal
    
# =========================================================
# COMPUTE VERTICAL COUNT
# =========================================================
def compute_vertical_count(cols, box_size, reversal=3):

    if not cols:
        return 0.0

    lengths = [len(col) for _, col in cols if col]

    if not lengths:
        return 0.0

    avg_length = np.mean(lengths)

    return avg_length * box_size * reversal
    
# =========================================================
# COMPUTE OBJECTIVES
# =========================================================

def compute_pnf_price_objectives(cols, levels, box_size, reversal):

    resistance = levels.get("resistance", [])
    support = levels.get("support", [])

    if not resistance or not support:
        return {}

    breakout_up = max(resistance) if resistance else None
    breakdown_down = min(support) if support else None

    width = max(resistance) - min(support)

    return {
        # base structure range projection
        "range_target_up": breakout_up + width if breakout_up else None,
        "range_target_down": breakdown_down - width if breakdown_down else None,

        # classical PNF box projection
        "box_target_up": breakout_up + (len(cols) * box_size),
        "box_target_down": breakdown_down - (len(cols) * box_size),

        # structural symmetry target
        "mid_extension_up": breakout_up + (width * 1.5),
        "mid_extension_down": breakdown_down - (width * 1.5)
    }
    
# =========================================================
# DETECT TRIPLE TOP
# =========================================================
def detect_triple_top(cols):

    if not cols or len(cols) < 3:
        return 0

    count = 0

    for i in range(2, len(cols)):

        try:
            if (
                cols[i][0] == "X"
                and cols[i-1][0] == "O"
                and cols[i-2][0] == "X"
            ):

                if max(cols[i][1]) > max(cols[i-2][1]):
                    count += 1
        except:
            continue

    return count
    
# =========================================================
# DETECT TRIPLE BOTTOM
# =========================================================
def detect_triple_bottom(cols):

    if not cols or len(cols) < 3:
        return 0

    count = 0

    for i in range(2, len(cols)):

        try:
            if (
                cols[i][0] == "O"
                and cols[i-1][0] == "X"
                and cols[i-2][0] == "O"
            ):

                if min(cols[i][1]) < min(cols[i-2][1]):
                    count += 1
        except:
            continue

    return count
    
# =========================================================
# DETECT SPRINGS
# =========================================================
def detect_springs(cols):

    if not cols or len(cols) < 3:
        return 0

    springs = 0

    for i in range(1, len(cols)):

        prev_dir, prev_col = cols[i - 1]
        cur_dir, cur_col = cols[i]

        if prev_dir == "O" and cur_dir == "X":

            prev_support = min(prev_col)
            cur_low = min(cur_col)

            # true spring = undercut then reclaim
            if cur_low < prev_support:
                springs += 1

    return springs
    
# =========================================================
# DETECT UPTHRUSTS
# =========================================================
def detect_upthrusts(cols):

    if not cols or len(cols) < 3:
        return 0

    upthrusts = 0

    for i in range(1, len(cols)):

        prev_dir, prev_col = cols[i - 1]
        cur_dir, cur_col = cols[i]

        if prev_dir == "X" and cur_dir == "O":

            prev_resistance = max(prev_col)
            cur_high = max(cur_col)

            # true upthrust = breakout above resistance then failure
            if cur_high > prev_resistance:
                upthrusts += 1

    return upthrusts
    
# =========================================================
# POINT & FIGURE ENGINE
# =========================================================

class PointFigureEngine:

    def __init__(self, box_size=1.0, reversal=3):
        self.box = box_size
        self.rev = reversal

    def _b(self, p):
        if p is None:
            return 0
        return int(p / self.box)

    def build(self, highs, lows, closes):

        if len(closes) == 0:
            return []

        cols = []
        direction = None

        last_high = self._b(closes[0])
        last_low = self._b(closes[0])

        current_col = []

        for i in range(len(closes)):

            h = self._b(highs[i])
            l = self._b(lows[i])

            # --------------------------
            # INITIALIZATION
            # --------------------------
            if direction is None:
                direction = "X"
                current_col.append(h)
                last_high = h
                last_low = l
                continue

            # --------------------------
            # X COLUMN (UP)
            # --------------------------
            if direction == "X":

                if h > last_high:
                    for b in range(last_high + 1, h + 1):
                        current_col.append(b)
                    last_high = h

                # reversal requires FULL box move
                if l <= last_high - self.rev:
                    cols.append(("X", current_col.copy()))
                    current_col = []
                    direction = "O"
                    last_low = l
                    current_col.append(last_low)

            # --------------------------
            # O COLUMN (DOWN)
            # --------------------------
            else:

                if l < last_low:
                    for b in range(last_low - 1, l - 1, -1):
                        current_col.append(b)
                    last_low = l

                if h >= last_low + self.rev:
                    cols.append(("O", current_col.copy()))
                    current_col = []
                    direction = "X"
                    last_high = h
                    current_col.append(last_high)

        if current_col:
            cols.append((direction, current_col))

        return cols

# =========================================================
# PNF LEVEL DETECTION (NEW)
# =========================================================

def detect_pnf_levels(cols):
    if not cols:
        return {"support": [], "resistance": []}

    support = []
    resistance = []

    for direction, col in cols:
        level = col[-1] if col else None
        if level is None:
            continue

        if direction == "X":
            resistance.append(level)
        else:
            support.append(level)

    return {
        "support": support[-10:],
        "resistance": resistance[-10:]
    }


# =========================================================
# PNF TARGET ENGINE (NEW CORE FEATURE)
# =========================================================
def compute_pnf_targets(levels, cols, box_size=1.0):

    support = levels.get("support", [])
    resistance = levels.get("resistance", [])

    if not support or not resistance or not cols:
        return {
            "support": None,
            "resistance": None,
            "horizontal_target": None,
            "vertical_target": None,
            "range_width": None,
            "count_target": None
        }

    support_val = min(support)
    resistance_val = max(resistance)

    # structural range
    width = resistance_val - support_val

    # -----------------------------
    # P&F CLASSIC COUNT METHOD
    # -----------------------------
    # horizontal count = congestion columns near breakout zone
    congestion_cols = sum(
        1 for _, col in cols[-10:]
        if len(col) >= 3
    )

    count_target = resistance_val + (congestion_cols * box_size)

    # -----------------------------
    # STANDARD PROJECTIONS
    # -----------------------------
    horizontal_target = resistance_val + width
    vertical_target = resistance_val + (width * 1.5)

    return {
        "support": support_val,
        "resistance": resistance_val,
        "range_width": width,

        # REAL TARGET ENGINE OUTPUT
        "horizontal_target": horizontal_target,
        "vertical_target": vertical_target,
        "count_target": count_target
    }

# =========================================================
# PNF SIGNAL ENGINE (NEW)
# =========================================================
def detect_pnf_signals(cols, resistance, support, volume_confirmed=False):

    if not cols:
        return {"signal": "NO DATA", "strength": 0.0}

    last_dir, last_col = cols[-1]

    if not last_col:
        return {"signal": "NEUTRAL", "strength": 0.0}

    last_val = last_col[-1]

    resistance = resistance or 0
    support = support or 0

    signal = "NEUTRAL"
    strength = 0.0

    # =========================
    # X COLUMN (DEMAND)
    # =========================
    if last_dir == "X":

        if resistance and last_val >= resistance:
            signal = "BREAKOUT"
            strength = 0.9

        elif len(cols) >= 3 and cols[-2][0] == "O":
            signal = "REVERSAL BULLISH"
            strength = 0.7

    # =========================
    # O COLUMN (SUPPLY)
    # =========================
    elif last_dir == "O":

        if support and last_val <= support:
            signal = "BREAKDOWN"
            strength = 0.9

        elif len(cols) >= 3 and cols[-2][0] == "X":
            signal = "REVERSAL BEARISH"
            strength = 0.7

    # =========================
    # VOLUME CONFIRMATION LAYER
    # =========================
    if volume_confirmed and signal in [
        "BREAKOUT",
        "BREAKDOWN",
        "REVERSAL BULLISH",
        "REVERSAL BEARISH"
    ]:
        strength = min(1.0, strength + 0.1)

    return {
        "signal": signal,
        "strength": strength
    }
    
# =========================================================
# P&F + VOLUME ALIGNMENT SCORE
# =========================================================
def compute_pnf_volume_alignment(cols, df):

    vol = df["Volume"].values

    if not cols or len(vol) < 10:
        return 0.0

    score = 0.0
    count = 0

    for i, (direction, column) in enumerate(cols):

        if i >= len(vol) or not column:
            continue

        window_start = max(0, i - 10)
        avg_vol = np.mean(vol[window_start:i + 1])

        if avg_vol == 0:
            continue

        vol_ratio = vol[i] / avg_vol

        if direction == "X":
            if vol_ratio >= 1.25:
                score += 1.0
            elif vol_ratio <= 0.8:
                score -= 0.5

        elif direction == "O":
            if vol_ratio >= 1.25:
                score -= 1.0
            elif vol_ratio <= 0.8:
                score += 0.5

        count += 1

    return score / count if count else 0.0
    
# =========================================================
# PNF STRUCTURE ANALYSIS (INSTITUTIONAL EXPANDED)
# =========================================================

def analyze_pnf(
    df,
    box_size=1.0,
    reversal=3
):

    high = df["High"].values
    low = df["Low"].values
    close = df["Close"].values

    engine = PointFigureEngine(
        box_size=box_size,
        reversal=reversal
    )

    cols = engine.build(
        high,
        low,
        close
    )

    volume_analysis = analyze_volume(df)

    volume_alignment = compute_pnf_volume_alignment(cols, df)

    volume_confirmed_breakout = is_volume_confirmed_breakout(cols, df)

    if not cols:
        return {
            "columns": 0,
            "direction": "NO DATA",
            "breakouts": 0,
            "breakdowns": 0,
            "double_top_breakouts": 0,
            "triple_top_breakouts": 0,
            "double_bottom_breakdowns": 0,
            "triple_bottom_breakdowns": 0,
            "springs": 0,
            "upthrusts": 0,
            "bull_traps": 0,
            "bear_traps": 0,
            "levels": {
                "support": [],
                "resistance": []
            },
            "targets": {},
            "signals": {
                "signal": "NO DATA",
                "strength": 0.0
            },
            "structure": [],
            "volume": {
                "state": volume_analysis["state"],
                "trend": volume_analysis["trend"],
                "alignment_score": volume_alignment,
                "breakout_confirmed": volume_confirmed_breakout
            },            
        }

    # =====================================================
    # CORE STRUCTURE
    # =====================================================

    direction = cols[-1][0]

    breakouts = sum(
        1 for c in cols
        if c[0] == "X"
    )

    breakdowns = sum(
        1 for c in cols
        if c[0] == "O"
    )

    # =====================================================
    # SUPPORT / RESISTANCE
    # =====================================================

    levels = detect_pnf_levels(cols)

    # =====================================================
    # PATTERN DETECTION
    # =====================================================

    triple_top_breakouts = detect_triple_top(cols)

    triple_bottom_breakdowns = detect_triple_bottom(cols)

    springs = detect_springs(cols)

    upthrusts = detect_upthrusts(cols)

    # =====================================================
    # SIMPLE DOUBLE COUNTS
    # =====================================================

    double_top_breakouts = max(
        triple_top_breakouts,
        breakouts // 2
    )

    double_bottom_breakdowns = max(
        triple_bottom_breakdowns,
        breakdowns // 2
    )

    # =====================================================
    # HORIZONTAL COUNT
    # =====================================================

    horizontal_count = compute_horizontal_count(
        cols,
        box_size
    )

    # =====================================================
    # VERTICAL COUNT
    # =====================================================

    vertical_count = compute_vertical_count(
        cols,
        box_size
    )

    # =====================================================
    # TARGET ENGINE
    # =====================================================

    pnf_objectives = compute_pnf_targets(
        levels,
        cols,
        box_size
    )

    targets = {
        "support": pnf_objectives.get("support"),
        "resistance": pnf_objectives.get("resistance"),

        # core projections
        "horizontal_target": pnf_objectives.get("horizontal_target"),
        "vertical_target": pnf_objectives.get("vertical_target"),
        "count_target": pnf_objectives.get("count_target"),
    }   

    resistance = pnf_objectives.get("resistance")
    support = pnf_objectives.get("support")

    if resistance is not None:

        targets["horizontal_count"] = horizontal_count
        targets["vertical_count"] = vertical_count

        targets["bull_objective"] = (
            resistance + horizontal_count
            if horizontal_count is not None
            else None
        )

        targets["extended_bull_objective"] = (
            resistance + vertical_count
            if vertical_count is not None
            else None
        )

    if support is not None:

        targets["bear_objective"] = (
            support - horizontal_count
            if horizontal_count is not None
            else None
        )

        targets["extended_bear_objective"] = (
            support - vertical_count
            if vertical_count is not None
            else None
        )

    # =====================================================
    # SIGNAL ENGINE
    # =====================================================

    signals = detect_pnf_signals(
        cols,
        resistance if resistance else 0,
        support if support else 0,
        volume_confirmed=volume_confirmed_breakout
    )

    # =====================================================
    # TRAP DETECTION
    # =====================================================

    bull_traps = 0
    bear_traps = 0

    if (
        signals.get("signal") == "BREAKOUT"
        and direction == "O"
    ):
        bull_traps += 1

    if (
        signals.get("signal") == "BREAKDOWN"
        and direction == "X"
    ):
        bear_traps += 1

    # =====================================================
    # STRUCTURE SNAPSHOT
    # =====================================================

    structure_snapshot = (
        cols[-10:]
        if len(cols) >= 10
        else cols
    )

    # =====================================================
    # RETURN
    # =====================================================

    return {

        # ---------------------------------------------
        # CORE
        # ---------------------------------------------
        "columns": len(cols),
        "direction": direction,

        # ---------------------------------------------
        # BREAKOUTS
        # ---------------------------------------------
        "breakouts": breakouts,
        "breakdowns": breakdowns,

        # ---------------------------------------------
        # PATTERNS
        # ---------------------------------------------
        "double_top_breakouts":
            double_top_breakouts,

        "triple_top_breakouts":
            triple_top_breakouts,

        "double_bottom_breakdowns":
            double_bottom_breakdowns,

        "triple_bottom_breakdowns":
            triple_bottom_breakdowns,

        # ---------------------------------------------
        # WYCKOFF EVENTS
        # ---------------------------------------------
        "springs": springs,
        "upthrusts": upthrusts,

        # ---------------------------------------------
        # TRAPS
        # ---------------------------------------------
        "bull_traps": bull_traps,
        "bear_traps": bear_traps,

        # ---------------------------------------------
        # LEVELS
        # ---------------------------------------------
        "levels": levels,

        # ---------------------------------------------
        # TARGETS
        # ---------------------------------------------
        "targets": targets,

        # ---------------------------------------------
        # SIGNALS
        # ---------------------------------------------
        "signals": signals,

        # ---------------------------------------------
        # COLUMN SNAPSHOT
        # ---------------------------------------------
        "structure": structure_snapshot
    }
    
# =========================================================
# WYCKOFF ANALYSIS
# =========================================================

def analyze_wyckoff(df):

    vol = df["Volume"].values
    price = df["Close"].values

    v_slope = poly_slope(vol)
    p_slope = poly_slope(price)

    compression = (df["High"].max() - df["Low"].min()) / df["Close"].iloc[-1]

    phase = (
        "ACCUMULATION" if v_slope < 0 and p_slope >= 0 else
        "DISTRIBUTION" if v_slope < 0 and p_slope < 0 else
        "MARKUP" if v_slope > 0 and p_slope > 0 else
        "MARKDOWN"
    )

    return {
        "volume_slope": v_slope,
        "price_slope": p_slope,
        "compression": compression,
        "phase": phase
    }


# =========================================================
# TIMEFRAME ANALYSIS ENGINE
# =========================================================

def analyze_timeframe(df):

    return {
        "trend": "BULLISH" if df["Close"].iloc[-1] > df["Close"].mean() else "BEARISH",
        "vol_state": "EXPANDING" if df["Volume"].iloc[-1] > df["Volume"].mean() else "CONTRACTING",
        "range": {
            "high": df["High"].max(),
            "low": df["Low"].min(),
            "close": df["Close"].iloc[-1]
        }
    }


# =========================================================
# MULTI-TIMEFRAME CONFLUENCE ENGINE
# =========================================================

def compute_confluence(mtf):

    bull = 0
    bear = 0
    compression_total = 0

    for tf, data in mtf.items():

        tf_an = analyze_timeframe(data)
        wy = analyze_wyckoff(data)

        compression_total += wy["compression"]

        if tf_an["trend"] == "BULLISH":
            bull += 1
        else:
            bear += 1

    total = len(mtf)

    if total == 0:
        return {
            "alignment": "NO DATA",
            "compression": 0,
            "confidence": 0,
            "bull_tf": 0,
            "bear_tf": 0
        }

    return {
        "alignment": "BULLISH" if bull > bear else "BEARISH",
        "compression": compression_total / total,
        "confidence": abs(bull - bear) / total,
        "bull_tf": bull,
        "bear_tf": bear
    }


# =========================================================
# INTERPRETATION LAYER
# =========================================================

def interpret(df, tf_analysis, wy, pnf, confluence):

    return {
        "bull": f"Break above {df['High'].max():.2f} continues expansion",
        "bear": f"Break below {df['Low'].min():.2f} triggers distribution",
        "risk": [],
        "bias": confluence["alignment"]
    }


# =========================================================
# MAIN ANALYSIS ENGINE (FIXED SIGNATURE)
# =========================================================

def run_wyckoff_pnf_analysis(
    ticker,
    timeframe="daily",
    box_size=1.0,
    reversal=3
):
    """
    FIXED:
    - Accepts timeframe, box_size, reversal
    - Prevents keyword argument crashes
    - Backward compatible
    """

    mtf = load_multi_timeframe(ticker)

    if not mtf:
        return {"error": "No data"}

    results = {}

    for tf, df in mtf.items():

        tf_analysis = analyze_timeframe(df)
        wy = analyze_wyckoff(df)
        pnf = analyze_pnf(df)

        results[tf] = {
            "timeframe_analysis": tf_analysis,
            "wyckoff": wy,
            "pnf": pnf
        }

    confluence = compute_confluence(mtf)

    return {
        "ticker": ticker,
        "timeframe": timeframe,
        "box_size": box_size,
        "reversal": reversal,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "timeframes": results,
        "confluence": confluence
    }


# =========================================================
# JOURNAL FORMATTER
# =========================================================

def format_for_journal(result):

    if "error" in result:
        return result["error"]

    out = []
    out.append("==========================================================")
    out.append("WYCKOFF POINT & FIGURE ANALYSIS")
    out.append("==========================================================")

    for tf, data in result["timeframes"].items():

        ta = data["timeframe_analysis"]
        wy = data["wyckoff"]
        pnf = data["pnf"]

        targets = pnf.get("targets", {})
        levels = pnf.get("levels", {})
        signals = pnf.get("signals", {})

        support_levels = levels.get("support", [])
        resistance_levels = levels.get("resistance", [])

        out.append("")
        out.append("==========================================================")
        out.append(f"{tf.upper()} ANALYSIS")
        out.append("==========================================================")

        # =====================================================
        # TIMEFRAME STRUCTURE
        # =====================================================

        out.append("TIMEFRAME STRUCTURE")

        out.append(
            f"Trend: {ta['trend']}"
        )

        out.append(
            f"Volume State: {ta['vol_state']}"
        )

        out.append(
            f"High: {ta['range']['high']:.2f}"
        )

        out.append(
            f"Low: {ta['range']['low']:.2f}"
        )

        out.append(
            f"Close: {ta['range']['close']:.2f}"
        )

        # =====================================================
        # WYCKOFF
        # =====================================================

        out.append("")
        out.append("WYCKOFF ANALYSIS")

        out.append(
            f"Phase: {wy['phase']}"
        )

        out.append(
            f"Compression: {wy['compression']:.4f}"
        )

        out.append(
            f"Price Slope: {wy['price_slope']:.4f}"
        )

        out.append(
            f"Volume Slope: {wy['volume_slope']:.4f}"
        )

        # =====================================================
        # PNF STRUCTURE
        # =====================================================

        out.append("")
        out.append("POINT & FIGURE STRUCTURE")

        out.append(
            f"Columns: {pnf['columns']}"
        )

        out.append(
            f"Direction: {pnf['direction']}"
        )

        out.append(
            f"Breakouts: {pnf['breakouts']}"
        )

        out.append(
            f"Breakdowns: {pnf['breakdowns']}"
        )

        out.append(
            f"Double Top Breakouts: "
            f"{pnf['double_top_breakouts']}"
        )

        out.append(
            f"Triple Top Breakouts: "
            f"{pnf['triple_top_breakouts']}"
        )

        out.append(
            f"Double Bottom Breakdowns: "
            f"{pnf['double_bottom_breakdowns']}"
        )

        out.append(
            f"Triple Bottom Breakdowns: "
            f"{pnf['triple_bottom_breakdowns']}"
        )

        out.append(
            f"Springs: {pnf['springs']}"
        )

        out.append(
            f"Upthrusts: {pnf['upthrusts']}"
        )

        out.append(
            f"Bull Traps: {pnf['bull_traps']}"
        )

        out.append(
            f"Bear Traps: {pnf['bear_traps']}"
        )

        # =====================================================
        # LEVELS
        # =====================================================

        out.append("")
        out.append("SUPPORT / RESISTANCE")

        if support_levels:
            out.append(
                "Support Levels: "
                + ", ".join(
                    str(x)
                    for x in support_levels[-5:]
                )
            )
        else:
            out.append(
                "Support Levels: N/A"
            )

        if resistance_levels:
            out.append(
                "Resistance Levels: "
                + ", ".join(
                    str(x)
                    for x in resistance_levels[-5:]
                )
            )
        else:
            out.append(
                "Resistance Levels: N/A"
            )

        # =====================================================
        # TARGETS
        # =====================================================

        out.append("")
        out.append("POINT & FIGURE OBJECTIVES")

        if targets:

            if targets.get("horizontal_count") is not None:
                out.append(
                    f"Horizontal Count: "
                    f"{targets['horizontal_count']:.2f}"
                )

            if targets.get("vertical_count") is not None:
                out.append(
                    f"Vertical Count: "
                    f"{targets['vertical_count']:.2f}"
                )

            if targets.get("bull_objective") is not None:
                out.append(
                    f"Bull Objective: "
                    f"{targets['bull_objective']:.2f}"
                )

            if targets.get("extended_bull_objective") is not None:
                out.append(
                    f"Extended Bull Objective: "
                    f"{targets['extended_bull_objective']:.2f}"
                )

            if targets.get("bear_objective") is not None:
                out.append(
                    f"Bear Objective: "
                    f"{targets['bear_objective']:.2f}"
                )

            if targets.get("extended_bear_objective") is not None:
                out.append(
                    f"Extended Bear Objective: "
                    f"{targets['extended_bear_objective']:.2f}"
                )
                
            if targets.get("horizontal_target") is not None:
                out.append(f"Horizontal Target: {targets['horizontal_target']:.2f}")

            if targets.get("vertical_target") is not None:
                out.append(f"Vertical Target: {targets['vertical_target']:.2f}")

            if targets.get("count_target") is not None:
                out.append(f"Count Target (Congestion Projection): {targets['count_target']:.2f}")                

        # =====================================================
        # SIGNALS
        # =====================================================

        out.append("")
        out.append("POINT & FIGURE SIGNALS")

        out.append(
            f"Signal: "
            f"{signals.get('signal', 'N/A')}"
        )

        out.append(
            f"Strength: "
            f"{signals.get('strength', 0):.2f}"
        )
        
        # =====================================================
        # PNF INTERPRETATION
        # =====================================================

        out.append("")
        out.append("POINT & FIGURE INTERPRETATION")       

        signal = signals.get("signal", "N/A")

        if signal == "BREAKOUT":

            out.append(
                "P&F Interpretation: "
                "Bullish breakout currently active."
            )

        elif signal == "BREAKDOWN":

            out.append(
                "P&F Interpretation: "
                "Bearish breakdown currently active."
            )

        elif signal == "REVERSAL BULLISH":

            out.append(
                "P&F Interpretation: "
                "Bullish reversal structure forming."
            )

        elif signal == "REVERSAL BEARISH":

            out.append(
                "P&F Interpretation: "
                "Bearish reversal structure forming."
            )

        else:

            out.append(
                "P&F Interpretation: "
                "Neutral structure."
            )

        close_price = ta["range"]["close"]

        bull_obj = targets.get("bull_objective")
        bear_obj = targets.get("bear_objective")

        if bull_obj is not None:

            upside = (
                (bull_obj - close_price)
                / close_price
            ) * 100

            out.append(
                f"Upside To Bull Objective: "
                f"{upside:.2f}%"
            )

        if bear_obj is not None:

            downside = (
                (close_price - bear_obj)
                / close_price
            ) * 100

            out.append(
                f"Downside To Bear Objective: "
                f"{downside:.2f}%"
            )

        out.append("")
        out.append("WYCKOFF CONFIRMATION")

        if (
            wy["phase"] in ["ACCUMULATION", "MARKUP"]
            and signal in [
                "BREAKOUT",
                "REVERSAL BULLISH"
            ]
        ):

            out.append(
                "Wyckoff confirms bullish P&F structure."
            )

        elif (
            wy["phase"] in ["DISTRIBUTION", "MARKDOWN"]
            and signal in [
                "BREAKDOWN",
                "REVERSAL BEARISH"
            ]
        ):

            out.append(
                "Wyckoff confirms bearish P&F structure."
            )

        else:

            out.append(
                "Wyckoff and P&F currently diverging."
            )

        out.append("")
        out.append("PATTERN SIGNIFICANCE")

        if pnf["springs"] > 0:

            out.append(
                f"{pnf['springs']} spring event(s) detected "
                "suggesting accumulation."
            )

        if pnf["upthrusts"] > 0:

            out.append(
                f"{pnf['upthrusts']} upthrust event(s) detected "
                "suggesting distribution."
            )

        if pnf["triple_top_breakouts"] > 0:

            out.append(
                f"{pnf['triple_top_breakouts']} triple-top breakout(s) detected."
            )

        if pnf["triple_bottom_breakdowns"] > 0:

            out.append(
                f"{pnf['triple_bottom_breakdowns']} triple-bottom breakdown(s) detected."
            )

        out.append("")
        out.append("INSTITUTIONAL P&F SCORE")

        score = 50

        if signal == "BREAKOUT":
            score += 15

        if wy["phase"] == "MARKUP":
            score += 10

        if wy["phase"] == "ACCUMULATION":
            score += 10

        if pnf["springs"] > 0:
            score += 10

        if pnf["triple_top_breakouts"] > 0:
            score += 10

        if signal == "BREAKDOWN":
            score -= 15

        if wy["phase"] == "MARKDOWN":
            score -= 10

        if wy["phase"] == "DISTRIBUTION":
            score -= 10

        if pnf["upthrusts"] > 0:
            score -= 10

        if pnf["triple_bottom_breakdowns"] > 0:
            score -= 10

        score = max(0, min(100, score))

        out.append(
            f"Institutional Score: {score}/100"
        )

        out.append("")
        out.append("TRADE THESIS")

        if score >= 75:

            out.append(
                "Strong institutional accumulation characteristics "
                "with favorable P&F structure."
            )

        elif score >= 60:

            out.append(
                "Moderately bullish structure with acceptable confirmation."
            )

        elif score <= 25:

            out.append(
                "Strong distribution characteristics present."
            )

        elif score <= 40:

            out.append(
                "Bearish structure with weak accumulation evidence."
            )

        else:

            out.append(
                "Mixed signals. Additional confirmation required."
            )

    

    return "\n".join(out)
from typing import List, Dict, Any
import numpy as np

from modules.wyckoff.common import (
    FRACTAL_HIGH,
    FRACTAL_LOW,

    IMPULSE_WAVES,
    EXTENDED_IMPULSE_WAVES,
    CORRECTIVE_WAVES,
    EXTENDED_CORRECTIVE_WAVES,

    TREND_FRACTAL,
    REVERSAL_FRACTAL,
    LIQUIDITY_FRACTAL,
    BREAK_FRACTAL
)

from modules.wyckoff.schemas import (
    FractalPoint,
    ElliottWave,
    TimeframeContext
)

# =========================================================
# SAFE UTIL
# =========================================================

def safe_div(a, b):
    return float(a) / float(b) if b != 0 else 0.0


# =========================================================
# FRACTAL SORT
# =========================================================

def sort_fractals(fractals: List[FractalPoint]) -> List[FractalPoint]:
    return sorted(fractals, key=lambda f: f.index)


# =========================================================
# ZIGZAG SWING ENGINE (STRUCTURAL CLEANING)
# =========================================================

def extract_swings(fractals: List[FractalPoint]) -> List[FractalPoint]:

    fractals = sort_fractals(fractals)
    swings = []

    for f in fractals:

        if f.fractal_type not in (FRACTAL_HIGH, FRACTAL_LOW):
            continue

        if not swings:
            swings.append(f)
            continue

        last = swings[-1]

        # same direction collapse → keep extreme only
        if f.fractal_type == last.fractal_type:
            if f.fractal_type == FRACTAL_HIGH and f.price > last.price:
                swings[-1] = f
            elif f.fractal_type == FRACTAL_LOW and f.price < last.price:
                swings[-1] = f
            continue

        # enforce alternation (zigzag)
        swings.append(f)

    return swings


# =========================================================
# REGIME DETECTION (IMPULSE vs CORRECTIVE)
# =========================================================

def detect_regime(swings: List[FractalPoint]) -> str:

    if len(swings) < 5:
        return "CORRECTIVE"

    try:
        w1 = abs(swings[1].price - swings[0].price)
        w3 = abs(swings[3].price - swings[2].price)

        impulse_score = 0

        # wave expansion check
        if w3 > w1:
            impulse_score += 1

        # structure continuity
        if swings[2].fractal_type != swings[1].fractal_type:
            impulse_score += 1

        # displacement
        if abs(swings[4].price - swings[3].price) > 0:
            impulse_score += 1

        return "IMPULSE" if impulse_score >= 2 else "CORRECTIVE"

    except:
        return "CORRECTIVE"


# =========================================================
# LABEL SELECTOR (FULL COMMON.PY COMPLIANCE)
# =========================================================

def select_labels(swings: List[FractalPoint], regime: str):

    n = len(swings)

    if regime == "IMPULSE":

        if n > 8:
            return EXTENDED_IMPULSE_WAVES
        return IMPULSE_WAVES

    else:

        if n > 6:
            return EXTENDED_CORRECTIVE_WAVES
        return CORRECTIVE_WAVES


# =========================================================
# WAVE BUILDER (GENERIC MULTI-REGIME)
# =========================================================

def build_waves(swings: List[FractalPoint], labels: List[str]) -> List[ElliottWave]:

    waves = []

    for i in range(min(len(labels), len(swings))):

        s = swings[i]

        waves.append(
            ElliottWave(
                label=labels[i],
                start_index=s.index,
                end_index=s.index,
                start_price=s.price,
                end_price=s.price,
                timeframe=s.timeframe,
                confidence=0.0,
                metadata={
                    "degree": s.degree,
                    "role": s.metadata.get("role", None),
                    "fractal_type": s.fractal_type
                }
            )
        )

    return waves


# =========================================================
# IMPULSE VALIDATION
# =========================================================

def validate_impulse(waves: List[ElliottWave]) -> float:

    if len(waves) < 5:
        return 0.0

    w1, w2, w3, w4, w5 = waves[:5]

    score = 1.0

    # Wave 2 retrace rule
    if w2.end_price <= w1.start_price:
        score -= 0.3

    # Wave 3 strength rule
    l1 = abs(w2.end_price - w1.start_price)
    l2 = abs(w3.end_price - w2.end_price)
    l3 = abs(w4.end_price - w3.end_price)

    if l2 < min(l1, l3):
        score -= 0.4

    # Wave 4 overlap rule
    if w4.end_price <= w1.end_price:
        score -= 0.2

    return max(0.0, score)


# =========================================================
# MAIN ENGINE (MULTI-REGIME)
# =========================================================

def detect_wave_structure(context: TimeframeContext) -> Dict[str, Any]:

    swings = extract_swings(context.fractals)

    regime = detect_regime(swings)
    labels = select_labels(swings, regime)

    waves = build_waves(swings, labels)

    # ============================
    # IMPULSE PATH
    # ============================
    if regime == "IMPULSE":

        score = validate_impulse(waves)

        context.waves = waves
        context.score = score
        context.bias = "BULLISH" if score > 0.7 else "NEUTRAL"

        return {
            "valid": score >= 0.7,
            "regime": "IMPULSE",
            "score": score,
            "waves": [
                {
                    "label": w.label,
                    "price": w.start_price,
                    "role": w.metadata.get("role")
                }
                for w in waves
            ]
        }

    # ============================
    # CORRECTIVE PATH
    # ============================
    context.waves = waves
    context.score = 0.4
    context.bias = "NEUTRAL"

    return {
        "valid": False,
        "regime": regime,
        "score": 0.4,
        "waves": [
            {
                "label": w.label,
                "price": w.start_price,
                "role": w.metadata.get("role")
            }
            for w in waves
        ]
    }
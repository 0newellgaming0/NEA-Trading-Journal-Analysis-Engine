import numpy as np

from modules.wyckoff.common import (
    TradingRange,
    FractalPoint,

    FRACTAL_HIGH,
    FRACTAL_LOW,

    MINOR_FRACTAL,
    INTERMEDIATE_FRACTAL,
    MAJOR_FRACTAL,
    PRIMARY_FRACTAL,
    SUPER_FRACTAL,

    FIB_CONFLUENCE_ZONES,

    safe_float,
    safe_mean,
    safe_std,
    clamp_confidence
)


# =========================================================
# STRUCTURAL CONFIGURATION
# =========================================================

MIN_RANGE_FRACTALS = 4

STRUCTURAL_DEGREES = {
    INTERMEDIATE_FRACTAL,
    MAJOR_FRACTAL,
    PRIMARY_FRACTAL,
    SUPER_FRACTAL
}


# =========================================================
# SAFE HELPERS
# =========================================================

def get_fractal_price(fractal):
    try:
        return safe_float(fractal.price)
    except:
        return 0.0


def get_fractal_index(fractal):
    try:
        return int(fractal.index)
    except:
        return 0


def get_fractal_degree(fractal):
    try:
        return fractal.degree
    except:
        return MINOR_FRACTAL


# =========================================================
# FRACTAL FILTERING
# =========================================================

def filter_structural_fractals(fractals):
    """
    Removes noise-level fractals and retains
    structurally meaningful pivots.
    """

    filtered = []

    for fractal in fractals:

        degree = get_fractal_degree(fractal)

        if degree in STRUCTURAL_DEGREES:
            filtered.append(fractal)

    return filtered


# =========================================================
# SUPPORT / RESISTANCE DISCOVERY
# =========================================================

def extract_structural_levels(fractals):

    support_levels = []
    resistance_levels = []

    for fractal in fractals:

        if fractal.fractal_type == FRACTAL_LOW:
            support_levels.append(get_fractal_price(fractal))

        elif fractal.fractal_type == FRACTAL_HIGH:
            resistance_levels.append(get_fractal_price(fractal))

    return {
        "support_levels": support_levels,
        "resistance_levels": resistance_levels
    }


# =========================================================
# RANGE BOUNDARY DETECTION
# =========================================================

def detect_range_boundaries(fractals):

    if len(fractals) < MIN_RANGE_FRACTALS:
        return None

    prices = [
        get_fractal_price(f)
        for f in fractals
    ]

    highs = [
        get_fractal_price(f)
        for f in fractals
        if f.fractal_type == FRACTAL_HIGH
    ]

    lows = [
        get_fractal_price(f)
        for f in fractals
        if f.fractal_type == FRACTAL_LOW
    ]

    if not highs or not lows:
        return None

    return {
        "range_high": max(highs),
        "range_low": min(lows),
        "price_mean": safe_mean(prices),
        "price_std": safe_std(prices)
    }


# =========================================================
# COMPRESSION SCORING
# =========================================================

def calculate_compression_score(fractals):

    try:

        if len(fractals) < MIN_RANGE_FRACTALS:
            return 0.0

        prices = np.asarray(
            [
                get_fractal_price(f)
                for f in fractals
            ],
            dtype=float
        )

        mean_price = np.nanmean(prices)

        if mean_price <= 0:
            return 0.0

        coefficient_of_variation = (
            np.nanstd(prices)
            / mean_price
        )

        compression = (
            1.0
            - min(
                coefficient_of_variation,
                1.0
            )
        )

        return clamp_confidence(compression)

    except:
        return 0.0


# =========================================================
# EXPANSION SCORING
# =========================================================

def calculate_expansion_score(fractals):

    try:

        if len(fractals) < MIN_RANGE_FRACTALS:
            return 0.0

        prices = np.asarray(
            [
                get_fractal_price(f)
                for f in fractals
            ],
            dtype=float
        )

        mean_price = np.nanmean(prices)

        if mean_price <= 0:
            return 0.0

        coefficient_of_variation = (
            np.nanstd(prices)
            / mean_price
        )

        return clamp_confidence(
            min(
                coefficient_of_variation,
                1.0
            )
        )

    except:
        return 0.0


# =========================================================
# FIBONACCI CONFLUENCE
# =========================================================

def calculate_fib_confluence(range_high, range_low):

    try:

        width = range_high - range_low

        if width <= 0:
            return {
                "score": 0.0,
                "zones": []
            }

        zones = []

        for zone_name, zone_values in FIB_CONFLUENCE_ZONES.items():

            lower_ratio, upper_ratio = zone_values

            zones.append({
                "zone": zone_name,
                "lower_price": (
                    range_low
                    + width * lower_ratio
                ),
                "upper_price": (
                    range_low
                    + width * upper_ratio
                )
            })

        score = min(
            len(zones) / 6.0,
            1.0
        )

        return {
            "score": clamp_confidence(score),
            "zones": zones
        }

    except:
        return {
            "score": 0.0,
            "zones": []
        }


# =========================================================
# RANGE CONFIDENCE
# =========================================================

def calculate_range_confidence(
    fractals,
    compression_score,
    fib_score
):

    try:

        structural_count = len(fractals)

        structural_component = min(
            structural_count / 10.0,
            1.0
        )

        confidence = (
            structural_component * 0.50
            + compression_score * 0.25
            + fib_score * 0.25
        )

        return clamp_confidence(confidence)

    except:
        return 0.0


# =========================================================
# TRADING RANGE BUILDER
# =========================================================

def build_trading_range(
    fractals,
    timeframe
):

    boundaries = detect_range_boundaries(fractals)

    if boundaries is None:
        return None

    range_high = boundaries["range_high"]
    range_low = boundaries["range_low"]

    compression_score = calculate_compression_score(fractals)
    expansion_score = calculate_expansion_score(fractals)

    fib_data = calculate_fib_confluence(
        range_high,
        range_low
    )

    confidence = calculate_range_confidence(
        fractals,
        compression_score,
        fib_data["score"]
    )

    start_index = min(
        get_fractal_index(f)
        for f in fractals
    )

    end_index = max(
        get_fractal_index(f)
        for f in fractals
    )

    duration = (
        end_index
        - start_index
    )

    width = (
        range_high
        - range_low
    )

    major_count = len([
        f for f in fractals
        if f.degree == MAJOR_FRACTAL
    ])

    primary_count = len([
        f for f in fractals
        if f.degree == PRIMARY_FRACTAL
    ])

    return TradingRange(
        start_index=start_index,
        end_index=end_index,
        range_high=range_high,
        range_low=range_low,
        timeframe=timeframe,
        confidence=confidence,
        metadata={
            "width": width,
            "duration": duration,
            "compression_score": compression_score,
            "expansion_score": expansion_score,
            "fib_confluence_score": fib_data["score"],
            "fib_confluence_zones": fib_data["zones"],
            "fractal_count": len(fractals),
            "major_fractal_count": major_count,
            "primary_fractal_count": primary_count
        }
    )


# =========================================================
# MAIN RANGE ENGINE
# =========================================================

def detect_trading_ranges(
    fractals,
    timeframe,
    wave_result=None
):
    """
    Structural range engine.

    Consumes:
        - FractalPoint objects
        - Optional waveCounter output

    Produces:
        - TradingRange
        - support/resistance levels
        - compression metrics
        - expansion metrics
        - fibonacci confluence zones

    Does NOT:
        - classify Wyckoff events
        - classify phases
        - infer springs
        - infer UTADs
        - assign SOS/SOW/LPS/LPSY
    """

    structural_fractals = filter_structural_fractals(
        fractals
    )

    if len(structural_fractals) < MIN_RANGE_FRACTALS:

        return {
            "valid": False,
            "range": None,
            "support_levels": [],
            "resistance_levels": [],
            "compression_score": 0.0,
            "expansion_score": 0.0,
            "wave_alignment": False
        }

    trading_range = build_trading_range(
        structural_fractals,
        timeframe
    )

    levels = extract_structural_levels(
        structural_fractals
    )

    wave_alignment = False

    if wave_result:

        try:

            if wave_result.get("valid", False):

                wave_alignment = True

                trading_range.metadata[
                    "wave_structure_score"
                ] = wave_result.get(
                    "score",
                    0.0
                )

                trading_range.metadata[
                    "wave_fib_ratios"
                ] = wave_result.get(
                    "fib_ratios",
                    {}
                )

        except:
            pass

    return {
        "valid": True,
        "range": trading_range,
        "support_levels": levels["support_levels"],
        "resistance_levels": levels["resistance_levels"],
        "compression_score": trading_range.metadata.get(
            "compression_score",
            0.0
        ),
        "expansion_score": trading_range.metadata.get(
            "expansion_score",
            0.0
        ),
        "wave_alignment": wave_alignment
    }
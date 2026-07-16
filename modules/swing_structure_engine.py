"""
====================================================================
NEA28 SWING STRUCTURE ENGINE
Module:
    swing_structure_engine.py

Purpose
-------
Detects the most recent major swing high and major swing low.

Designed for:
- Risk Grid Engine
- Stop Loss Placement
- Wyckoff Structure
- Elliott Wave Reference Points
- Fibonacci Anchoring
- Supply/Demand Zones

Logic:
-------
Uses confirmed multi-bar pivots.

Major Swing High:
    Current high is greater than surrounding candles.

Major Swing Low:
    Current low is lower than surrounding candles.

No trading decisions are made here.
This module only identifies structure.

====================================================================
"""

import logging
from modules.eventEngine import extract_event_date


logger = logging.getLogger("swing_structure")


# =========================================================
# SAFE HELPERS
# =========================================================

def f(x):
    try:
        return float(x)
    except:
        return 0.0



# =========================================================
# SWING DETECTOR
# =========================================================

def detect_swing_point(df, index, strength=7):
    """
    Detect confirmed swing points.

    strength:
        Number of candles on each side.

        Example:
        strength=5

        Requires:
        5 candles before
        pivot candle
        5 candles after

    """

    if index < strength:
        return None

    if index >= len(df)-strength:
        return None


    high = f(df["High"].iloc[index])
    low = f(df["Low"].iloc[index])


    highs = [
        f(df["High"].iloc[i])
        for i in range(
            index-strength,
            index+strength+1
        )
    ]


    lows = [
        f(df["Low"].iloc[i])
        for i in range(
            index-strength,
            index+strength+1
        )
    ]



    # ==========================
    # MAJOR SWING HIGH
    # ==========================

    if high == max(highs):

        return {

            "type":"MAJOR_SWING_HIGH",

            "price":high,

            "high":high,

            "low":low,

            "index":index,

            "strength":strength

        }



    # ==========================
    # MAJOR SWING LOW
    # ==========================

    if low == min(lows):

        return {

            "type":"MAJOR_SWING_LOW",

            "price":low,

            "high":high,

            "low":low,

            "index":index,

            "strength":strength

        }


    return None



# =========================================================
# FIND MOST RECENT MAJOR STRUCTURE
# =========================================================

def find_major_swings(df, strength=5):

    swing_highs = []
    swing_lows = []

    for i in range(len(df)):

        swing = detect_swing_point(
            df,
            i,
            strength
        )

        if not swing:
            continue

        if swing["type"] == "MAJOR_SWING_HIGH":
            swing_highs.append(swing)

        elif swing["type"] == "MAJOR_SWING_LOW":
            swing_lows.append(swing)

    major_high = (
        swing_highs[-1]
        if swing_highs
        else None
    )

    latest_close = f(
        df["Close"].iloc[-1]
    )

    selected_low = None

    if swing_lows:

        latest_low = swing_lows[-1]

        # ------------------------------------
        # Normal situation
        # ------------------------------------

        if latest_close >= latest_low["price"]:

            selected_low = latest_low

        # ------------------------------------
        # Price has broken below latest swing
        # ------------------------------------

        else:

            for swing in reversed(swing_lows):

                if swing["price"] < latest_close:

                    selected_low = swing
                    break

            if selected_low is None:
                selected_low = swing_lows[0]

    return {

        "major_swing_high": major_high,

        "major_swing_low": selected_low,

        "all_swing_highs": swing_highs,

        "all_swing_lows": swing_lows

    }


# =========================================================
# STRUCTURE STATE
# =========================================================

def determine_market_structure(swings):

    high = swings.get(
        "major_swing_high"
    )

    low = swings.get(
        "major_swing_low"
    )


    if not high or not low:
        return "UNKNOWN"



    if high["index"] > low["index"]:
        return "RECENT_HIGH_FORMED"


    if low["index"] > high["index"]:
        return "RECENT_LOW_FORMED"



    return "NEUTRAL"



# =========================================================
# RISK GRID EXPORT
# =========================================================

def build_risk_grid_reference(swings):

    """
    Creates clean values for Risk Grid Engine.

    These values can be overridden manually.
    """

    high = swings.get(
        "major_swing_high"
    )

    low = swings.get(
        "major_swing_low"
    )


    return {


        "auto_last_high":

            high["price"]
            if high else None,



        "auto_low":

            low["price"]
            if low else None,



        "manual_override":

            False

    }



# =========================================================
# MAIN NEA PLUGIN CONTRACT
# =========================================================

def analyze_swing_structure(
        df,
        strength=5
):


    logger.info(
        "[SWING] structure analyzer started"
    )


    swings = find_major_swings(
        df,
        strength
    )


    structure = determine_market_structure(
        swings
    )


    risk_reference = build_risk_grid_reference(
        swings
    )



    event = {


        "id":
            extract_event_date(
                df,
                len(df)-1
            ),


        "type":
            "SWING_STRUCTURE",


        "detected":
            True,


        "status":
            "CONFIRMED",


        "structure":
            structure,


        "major_swing_high":
            swings["major_swing_high"],


        "major_swing_low":
            swings["major_swing_low"],



        "risk_grid_reference":
            risk_reference


    }



    return {


        "event":
            event,


        "trade":
            {},


        "regime":
            "MARKET_STRUCTURE"

    }
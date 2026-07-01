import logging

logger = logging.getLogger("bw_ao_ac")


# =========================================================
# SAFE HELPERS
# =========================================================
def f(x):
    try:
        return float(x)
    except:
        return 0.0


# =========================================================
# AO CALCULATOR
# =========================================================
def calculate_ao(df, i):

    try:
        if i < 33:
            return 0.0

        median = (df["High"] + df["Low"]) / 2.0

        fast = median.iloc[i - 4:i + 1].mean()
        slow = median.iloc[i - 33:i + 1].mean()

        return fast - slow

    except Exception:
        return 0.0


# =========================================================
# AC CALCULATOR
# =========================================================
def calculate_ac(df, i):

    try:
        if i < 37:
            return 0.0

        ao_vals = [
            calculate_ao(df, j)
            for j in range(i - 4, i + 1)
        ]

        return ao_vals[-1] - sum(ao_vals) / len(ao_vals)

    except Exception:
        return 0.0


# =========================================================
# SAUCER DETECTOR
# =========================================================
def detect_ao_saucer_buy(df, i):

    if i < 3:
        return False

    ao0 = calculate_ao(df, i)
    ao1 = calculate_ao(df, i - 1)
    ao2 = calculate_ao(df, i - 2)

    return (
        ao0 > 0 and ao1 > 0 and ao2 > 0 and
        ao2 > ao1 and ao0 > ao1 and ao0 > ao2
    )


def detect_ao_saucer_sell(df, i):

    if i < 3:
        return False

    ao0 = calculate_ao(df, i)
    ao1 = calculate_ao(df, i - 1)
    ao2 = calculate_ao(df, i - 2)

    return (
        ao0 < 0 and ao1 < 0 and ao2 < 0 and
        ao2 < ao1 and ao0 < ao1 and ao0 < ao2
    )


# =========================================================
# TWIN PEAKS DETECTOR
# =========================================================
def detect_twin_peaks_buy(df, i):

    if i < 6:
        return False

    ao = [calculate_ao(df, j) for j in range(i - 6, i + 1)]

    if max(ao) >= 0:
        return False

    troughs = [
        ao[k]
        for k in range(1, len(ao) - 1)
        if ao[k] < ao[k - 1] and ao[k] < ao[k + 1]
    ]

    if len(troughs) < 2:
        return False

    return troughs[-1] > troughs[-2] and ao[-1] > ao[-2]


def detect_twin_peaks_sell(df, i):

    if i < 6:
        return False

    ao = [calculate_ao(df, j) for j in range(i - 6, i + 1)]

    if min(ao) <= 0:
        return False

    peaks = [
        ao[k]
        for k in range(1, len(ao) - 1)
        if ao[k] > ao[k - 1] and ao[k] > ao[k + 1]
    ]

    if len(peaks) < 2:
        return False

    return peaks[-1] < peaks[-2] and ao[-1] < ao[-2]


# =========================================================
# ZONE ENGINE
# =========================================================
def resolve_bill_williams_type(ao, prev_ao, ac, prev_ac):

    ao_up = ao > prev_ao
    ao_down = ao < prev_ao
    ac_up = ac > prev_ac
    ac_down = ac < prev_ac

    green = ao_up and ac_up
    red = ao_down and ac_down
    gray = not green and not red

    if prev_ao < 0 and ao > 0:
        return "AO_ZERO_CROSS_BUY"

    if prev_ao > 0 and ao < 0:
        return "AO_ZERO_CROSS_SELL"

    if prev_ac < 0 and ac > 0:
        return "AC_BUY"

    if prev_ac > 0 and ac < 0:
        return "AC_SELL"

    if green:
        return "GREEN_ZONE"

    if red:
        return "RED_ZONE"

    if gray:
        return "GRAY_ZONE"

    return None


# =========================================================
# MOMENTUM SCORING
# =========================================================
def calculate_momentum_strength(ao, ac):

    strength = abs(ao) * 60 + abs(ac) * 40
    return min(100, strength * 10)


# =========================================================
# CONFIRMATION ENGINE (FRACTAL FILTER HOOK)
# =========================================================
def confirm_fractal_signal(signal_type, fractal_signal):

    if fractal_signal is None:
        return False

    if "BUY" in signal_type and fractal_signal == "BULLISH":
        return True

    if "SELL" in signal_type and fractal_signal == "BEARISH":
        return True

    return False


# =========================================================
# MAIN ANALYZER
# =========================================================
def analyze_momentum(df, fractal_signal=None):

    logger.info("[AO/AC] analyzer started")

    latest = None

    for i in range(len(df) - 1, -1, -1):

        ao = calculate_ao(df, i)
        ac = calculate_ac(df, i)

        prev_ao = calculate_ao(df, i - 1)
        prev_ac = calculate_ac(df, i - 1)

        signal = None

        if detect_twin_peaks_buy(df, i):
            signal = "AO_TWIN_PEAKS_BUY"

        elif detect_twin_peaks_sell(df, i):
            signal = "AO_TWIN_PEAKS_SELL"

        elif detect_ao_saucer_buy(df, i):
            signal = "AO_SAUCER_BUY"

        elif detect_ao_saucer_sell(df, i):
            signal = "AO_SAUCER_SELL"

        else:
            signal = resolve_bill_williams_type(ao, prev_ao, ac, prev_ac)

        if not signal:
            continue

        zone = "GREEN_ZONE" if ao > prev_ao and ac > prev_ac else \
               "RED_ZONE" if ao < prev_ao and ac < prev_ac else \
               "GRAY_ZONE"

        strength = calculate_momentum_strength(ao, ac)

        confidence = strength

        confirmed = confirm_fractal_signal(signal, fractal_signal)

        latest = {
            "id": i,
            "detected": True,
            "signal": signal,
            "zone": zone,
            "ao": ao,
            "ac": ac,
            "momentum_strength": strength,
            "confirmation": confirmed,
            "confidence": confidence,
            "regime": "MOMENTUM_ENGINE"
        }

        break

    if not latest:
        return {
            "event": {},
            "trade": {},
            "regime": "NONE"
        }

    return {
        "event": latest,
        "trade": {},
        "regime": "MOMENTUM_ENGINE"
    }
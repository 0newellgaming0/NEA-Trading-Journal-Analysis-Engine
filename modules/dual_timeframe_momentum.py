import numpy as np
from modules.ohlcv_normalizer import normalize_timestamp


# =========================================================
# DUAL TIMEFRAME MOMENTUM ENGINE (STANDALONE SYSTEM)
# Runs parallel to T-Line (no dependency on EMA-8 logic)
# =========================================================


class DualTimeframeMomentumEngine:
    """
    Independent momentum analysis engine that evaluates:
    - Higher timeframe momentum structure
    - Lower timeframe momentum structure
    - Cross-timeframe alignment
    - Regime classification
    """

    def __init__(self, fast_period=8, slow_period=21):
        self.fast_period = fast_period
        self.slow_period = slow_period

    # -----------------------------------------------------
    # CORE MOMENTUM CALCULATION (NO EXTERNAL DEPENDENCY)
    # -----------------------------------------------------
    def _calc_momentum(self, closes):
        """
        Returns normalized momentum series using rate-of-change.
        """
        closes = np.asarray(closes, dtype=float)

        if len(closes) < self.slow_period + 2:
            return np.array([])

        roc_fast = (closes[self.fast_period:] - closes[:-self.fast_period]) / closes[:-self.fast_period]
        roc_slow = (closes[self.slow_period:] - closes[:-self.slow_period]) / closes[:-self.slow_period]

        # align lengths
        min_len = min(len(roc_fast), len(roc_slow))
        roc_fast = roc_fast[-min_len:]
        roc_slow = roc_slow[-min_len:]

        momentum = (roc_fast * 0.6) + (roc_slow * 0.4)

        return momentum

    # -----------------------------------------------------
    # REGIME CLASSIFICATION
    # -----------------------------------------------------
    def _classify_regime(self, mom_htf, mom_ltf):
        """
        Classifies dual-timeframe structure into institutional regimes.
        """

        if len(mom_htf) == 0 or len(mom_ltf) == 0:
            return "INSUFFICIENT_DATA"

        htf = mom_htf[-1]
        ltf = mom_ltf[-1]

        alignment = np.sign(htf) == np.sign(ltf)

        strength = abs(htf) + abs(ltf)

        if alignment and htf > 0:
            if strength > 0.02:
                return "EXPANSION_UP"
            return "TREND_UP_MATURE"

        if alignment and htf < 0:
            if strength > 0.02:
                return "EXPANSION_DOWN"
            return "TREND_DOWN_MATURE"

        if not alignment:
            if abs(htf) > abs(ltf):
                return "HTF_DOMINANT_CONTRACTION"
            return "LTF_NOISE_PULLBACK"

        return "COMPRESSION"

    # -----------------------------------------------------
    # MAIN ANALYSIS ENTRY
    # -----------------------------------------------------
    def analyze(self, htf_data, ltf_data):
        """
        htf_data / ltf_data expected as OHLCV-like arrays:
        [timestamp, open, high, low, close, volume]
        """

        # normalize timestamps ONLY via central system (no raw datetime logic here)
        htf_data = np.array(htf_data, dtype=object)
        ltf_data = np.array(ltf_data, dtype=object)

        htf_closes = htf_data[:, 4].astype(float)
        ltf_closes = ltf_data[:, 4].astype(float)

        mom_htf = self._calc_momentum(htf_closes)
        mom_ltf = self._calc_momentum(ltf_closes)

        regime = self._classify_regime(mom_htf, mom_ltf)

        return {
            "regime": regime,
            "htf_momentum": float(mom_htf[-1]) if len(mom_htf) else None,
            "ltf_momentum": float(mom_ltf[-1]) if len(mom_ltf) else None,
            "alignment": np.sign(mom_htf[-1]) == np.sign(mom_ltf[-1]) if len(mom_htf) and len(mom_ltf) else None
        }


# =========================================================
# JOURNAL OUTPUT FORMATTER (NO TIME NORMALIZATION HERE)
# =========================================================

def format_dual_timeframe_report(result: dict) -> str:
    """
    Produces journal-ready output compatible with journal.py
    """

    regime = result.get("regime", "UNKNOWN")
    htf = result.get("htf_momentum")
    ltf = result.get("ltf_momentum")
    alignment = result.get("alignment")

    return (
        f"DUAL TIMEFRAME MOMENTUM ANALYSIS\n"
        f"--------------------------------\n"
        f"Regime: {regime}\n"
        f"HTF Momentum: {htf}\n"
        f"LTF Momentum: {ltf}\n"
        f"Alignment: {alignment}\n"
    )
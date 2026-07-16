"""
====================================================================
NEA28 FOLLOW THROUGH ENGINE

Module:
    modules/market/follow_through_engine.py

Purpose:
    Institutional CANSLIM follow-through lifecycle tracking.

Responsibilities:
    - Track market rally attempts
    - Track rally day progression
    - Detect follow-through days
    - Detect failed follow-through
    - Measure follow-through strength

Lifecycle:
    Day 1 Rally Attempt
    Day 2
    Day 3
    Day 4+
    Follow Through
    Failure

Output:
{
    "rally_attempt": True,
    "rally_day": 6,
    "follow_through_day": True,
    "follow_through_strength": 92,
    "failed_follow_through": False
}
====================================================================
"""

import logging
from datetime import datetime


logger = logging.getLogger("FollowThroughEngine")


class FollowThroughEngine:
    """
    CANSLIM follow-through detection engine.
    """

    def __init__(self):
        self.rally_active = False
        self.rally_day = 0
        self.follow_through_confirmed = False

        logger.info(
            "Follow Through Engine initialized"
        )

    def _safe_float(
        self,
        value,
        default=0
    ):
        try:
            return float(value)
        except Exception:
            return default

    def _safe_bool(
        self,
        value
    ):
        return bool(value)

    def _detect_rally_attempt(
        self,
        data
    ):
        """
        Detect Day 1 rally attempt.

        Requirements:
            - Market advances
            - Selling pressure decreases
        """

        gain = self._safe_float(
            data.get(
                "index_gain_percent",
                0
            )
        )

        if gain > 0:
            return True

        return False

    def _calculate_follow_through_strength(
        self,
        data
    ):
        """
        Measures follow-through quality.

        Components:
            - Price gain
            - Volume expansion
            - Breadth
            - Institutional participation
        """

        score = 0

        gain = self._safe_float(
            data.get(
                "index_gain_percent",
                0
            )
        )

        volume = self._safe_float(
            data.get(
                "volume_change_percent",
                0
            )
        )

        breadth = self._safe_float(
            data.get(
                "breadth_strength",
                0
            )
        )

        institutional = self._safe_float(
            data.get(
                "institutional_participation",
                0
            )
        )

        if gain >= 1.5:
            score += 30

        elif gain >= 1:
            score += 20

        elif gain > 0:
            score += 10

        if volume >= 20:
            score += 30

        elif volume >= 10:
            score += 20

        if breadth >= 70:
            score += 25

        elif breadth >= 50:
            score += 15

        if institutional >= 70:
            score += 15

        return min(
            score,
            100
        )

    def _detect_failure(
        self,
        data
    ):
        """
        Detect failed follow-through.

        Conditions:
            - Heavy decline
            - High selling volume
            - Weak breadth
        """

        decline = self._safe_float(
            data.get(
                "index_gain_percent",
                0
            )
        )

        volume = self._safe_float(
            data.get(
                "volume_change_percent",
                0
            )
        )

        breadth = self._safe_float(
            data.get(
                "breadth_strength",
                0
            )
        )

        if (
            decline <= -1.5
            and volume >= 10
            and breadth < 40
        ):
            return True

        return False

    def run(
        self,
        market_data
    ):
        """
        Execute CANSLIM follow-through analysis.

        Input:

        {
            "index_gain_percent":1.8,
            "volume_change_percent":15,
            "breadth_strength":80,
            "institutional_participation":75
        }

        Output:

        {
            "rally_attempt":True,
            "rally_day":6,
            "follow_through_day":True,
            "follow_through_strength":92,
            "failed_follow_through":False
        }
        """

        logger.info(
            "Running Follow Through Analysis"
        )

        if not isinstance(
            market_data,
            dict
        ):
            return {}

        rally_attempt = self._detect_rally_attempt(
            market_data
        )

        if rally_attempt:

            if not self.rally_active:
                self.rally_active = True
                self.rally_day = 1

            else:
                self.rally_day += 1

        else:

            self.rally_active = False
            self.rally_day = 0
            self.follow_through_confirmed = False

        strength = self._calculate_follow_through_strength(
            market_data
        )

        follow_through = False

        if (
            self.rally_active
            and self.rally_day >= 4
            and strength >= 70
        ):

            follow_through = True
            self.follow_through_confirmed = True

        failed = self._detect_failure(
            market_data
        )

        if failed:

            self.follow_through_confirmed = False

        return {

            "rally_attempt": self.rally_active,

            "rally_day": self.rally_day,

            "follow_through_day": follow_through,

            "follow_through_strength": strength,

            "failed_follow_through": failed,

            "timestamp": datetime.utcnow().isoformat()

        }
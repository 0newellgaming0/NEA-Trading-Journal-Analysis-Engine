"""
====================================================================
NEA28 MARKET STATE STORE

Module:
    modules/market/market_state_store.py

Purpose:
    Institutional market persistence layer.

Responsibilities:
    - Store market regime history
    - Store market snapshots
    - Store distribution events
    - Store follow-through events
    - Detect market state transitions
    - Provide historical market intelligence

Database:
    market_state.db

Tables:
    market_snapshots
    market_events
    market_regimes
    distribution_history
    follow_through_history

Output:
{
    "previous_state":"CORRECTION",
    "current_state":"CONFIRMED_UPTREND",
    "transition":"RECOVERY"
}
====================================================================
"""

import logging
import sqlite3
from datetime import datetime
from pathlib import Path


logger = logging.getLogger("MarketStateStore")


class MarketStateStore:
    """
    Institutional market persistence engine.
    """

    def __init__(
        self,
        database="market_state.db"
    ):
        self.database = Path(
            database
        )

        self._initialize_database()

        logger.info(
            "Market State Store initialized"
        )

    def _connect(self):
        return sqlite3.connect(
            self.database
        )

    def _initialize_database(self):
        with self._connect() as conn:

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS market_snapshots
                (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    market_score REAL,
                    market_state TEXT,
                    market_regime TEXT,
                    trend TEXT,
                    breadth_score REAL,
                    volatility_score REAL,
                    liquidity_score REAL,
                    confidence REAL
                )
                """
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS market_events
                (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    event_type TEXT,
                    severity INTEGER,
                    description TEXT
                )
                """
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS market_regimes
                (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    previous_state TEXT,
                    current_state TEXT,
                    transition TEXT
                )
                """
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS distribution_history
                (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    distribution_days INTEGER,
                    institutional_pressure REAL
                )
                """
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS follow_through_history
                (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    rally_day INTEGER,
                    follow_through INTEGER,
                    strength REAL
                )
                """
            )

            conn.commit()

    def _safe_float(
        self,
        value,
        default=0
    ):
        try:
            return float(value)
        except Exception:
            return default

    def _insert_snapshot(
        self,
        state
    ):
        with self._connect() as conn:

            conn.execute(
                """
                INSERT INTO market_snapshots
                (
                    timestamp,
                    market_score,
                    market_state,
                    market_regime,
                    trend,
                    breadth_score,
                    volatility_score,
                    liquidity_score,
                    confidence
                )
                VALUES
                (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    datetime.utcnow().isoformat(),
                    self._safe_float(
                        state.get(
                            "market_score",
                            0
                        )
                    ),
                    state.get(
                        "market_state",
                        "UNKNOWN"
                    ),
                    state.get(
                        "market_regime",
                        "UNKNOWN"
                    ),
                    state.get(
                        "trend",
                        "UNKNOWN"
                    ),
                    self._safe_float(
                        state.get(
                            "breadth_score",
                            0
                        )
                    ),
                    self._safe_float(
                        state.get(
                            "volatility_score",
                            0
                        )
                    ),
                    self._safe_float(
                        state.get(
                            "liquidity_score",
                            0
                        )
                    ),
                    self._safe_float(
                        state.get(
                            "confidence",
                            0
                        )
                    )
                )
            )

            conn.commit()

    def _get_previous_state(self):
        with self._connect() as conn:

            row = conn.execute(
                """
                SELECT market_state
                FROM market_snapshots
                ORDER BY id DESC
                LIMIT 1
                """
            ).fetchone()

        if row:
            return row[0]

        return "UNKNOWN"

    def _save_regime_transition(
        self,
        previous,
        current
    ):
        if previous == current:
            return

        with self._connect() as conn:

            conn.execute(
                """
                INSERT INTO market_regimes
                (
                    timestamp,
                    previous_state,
                    current_state,
                    transition
                )
                VALUES
                (?, ?, ?, ?)
                """,
                (
                    datetime.utcnow().isoformat(),
                    previous,
                    current,
                    self._determine_transition(
                        previous,
                        current
                    )
                )
            )

            conn.commit()

    def _determine_transition(
        self,
        previous,
        current
    ):
        if (
            previous == "CORRECTION"
            and
            current == "CONFIRMED_UPTREND"
        ):
            return "RECOVERY"

        if (
            current == "DISTRIBUTION"
        ):
            return "DETERIORATION"

        if (
            current == "DECLINE"
        ):
            return "BREAKDOWN"

        return "REGIME_CHANGE"

    def _save_events(
        self,
        events
    ):
        if not isinstance(
            events,
            list
        ):
            return

        with self._connect() as conn:

            for event in events:

                conn.execute(
                    """
                    INSERT INTO market_events
                    (
                        timestamp,
                        event_type,
                        severity,
                        description
                    )
                    VALUES
                    (?, ?, ?, ?)
                    """,
                    (
                        datetime.utcnow().isoformat(),
                        event.get(
                            "type",
                            "UNKNOWN"
                        ),
                        event.get(
                            "severity",
                            0
                        ),
                        event.get(
                            "description",
                            ""
                        )
                    )
                )

            conn.commit()

    def run(
        self,
        market_state
    ):
        """
        Store market intelligence state.

        Input:

        {
            "market_score":85,
            "market_state":"CONFIRMED_UPTREND",
            "market_regime":"EARLY_ADVANCE"
        }

        Output:

        {
            "previous_state":"CORRECTION",
            "current_state":"CONFIRMED_UPTREND",
            "transition":"RECOVERY"
        }
        """

        logger.info(
            "Updating Market State Store"
        )

        if not isinstance(
            market_state,
            dict
        ):
            return {}

        previous_state = self._get_previous_state()

        current_state = market_state.get(
            "market_state",
            "UNKNOWN"
        )

        self._insert_snapshot(
            market_state
        )

        self._save_regime_transition(
            previous_state,
            current_state
        )

        self._save_events(
            market_state.get(
                "events",
                []
            )
        )

        return {

            "previous_state": previous_state,

            "current_state": current_state,

            "transition": self._determine_transition(
                previous_state,
                current_state
            ),

            "timestamp": datetime.utcnow().isoformat()

        }
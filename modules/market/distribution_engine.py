"""
====================================================================
NEA28 MARKET DISTRIBUTION TRACKING ENGINE

Module:
    modules/market/distribution_engine.py

Purpose:
    Institutional CANSLIM distribution tracking.

Responsibilities:
    - Detect distribution days
    - Track stall days
    - Track churning activity
    - Persist institutional selling events
    - Measure market selling pressure

Database:
    market_events.db

Table:
    distribution_events

Schema:
    date
    index
    event_type
    volume_change
    price_change
    severity
    active

Output:
{
    "distribution_days":3,
    "stall_days":1,
    "churning_days":2,
    "institutional_pressure":42
}
====================================================================
"""

import logging
import sqlite3
from datetime import datetime
from pathlib import Path


logger = logging.getLogger("DistributionTrackingEngine")


class DistributionTrackingEngine:
    """
    Institutional CANSLIM distribution tracking engine.
    """

    def __init__(
        self,
        database="market_events.db"
    ):
        self.database = Path(database)
        self._initialize_database()

        logger.info(
            "Distribution Tracking Engine initialized"
        )

    def _connect(self):
        return sqlite3.connect(
            self.database
        )

    def _initialize_database(self):
        with self._connect() as conn:

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS distribution_events
                (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT,
                    index_name TEXT,
                    event_type TEXT,
                    volume_change REAL,
                    price_change REAL,
                    severity INTEGER,
                    active INTEGER
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

    def _detect_distribution_day(
        self,
        data
    ):
        price_change = self._safe_float(
            data.get(
                "price_change",
                0
            )
        )

        volume_change = self._safe_float(
            data.get(
                "volume_change",
                0
            )
        )

        if (
            price_change < 0
            and volume_change > 0
        ):
            return True

        return False

    def _detect_stall_day(
        self,
        data
    ):
        price_change = self._safe_float(
            data.get(
                "price_change",
                0
            )
        )

        volume_change = self._safe_float(
            data.get(
                "volume_change",
                0
            )
        )

        if (
            abs(price_change) < 0.5
            and volume_change > 10
        ):
            return True

        return False

    def _detect_churning(
        self,
        data
    ):
        price_change = self._safe_float(
            data.get(
                "price_change",
                0
            )
        )

        volume_change = self._safe_float(
            data.get(
                "volume_change",
                0
            )
        )

        if (
            abs(price_change) < 1
            and volume_change > 20
        ):
            return True

        return False

    def _calculate_severity(
        self,
        data
    ):
        severity = 0

        volume_change = self._safe_float(
            data.get(
                "volume_change",
                0
            )
        )

        price_change = self._safe_float(
            data.get(
                "price_change",
                0
            )
        )

        if volume_change >= 25:
            severity += 40

        elif volume_change >= 10:
            severity += 20

        if price_change <= -2:
            severity += 40

        elif price_change < 0:
            severity += 20

        return min(
            severity,
            100
        )

    def _save_event(
        self,
        index_name,
        event_type,
        data,
        severity
    ):
        with self._connect() as conn:

            conn.execute(
                """
                INSERT INTO distribution_events
                (
                    date,
                    index_name,
                    event_type,
                    volume_change,
                    price_change,
                    severity,
                    active
                )
                VALUES
                (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    datetime.utcnow().isoformat(),
                    index_name,
                    event_type,
                    self._safe_float(
                        data.get(
                            "volume_change",
                            0
                        )
                    ),
                    self._safe_float(
                        data.get(
                            "price_change",
                            0
                        )
                    ),
                    severity,
                    1
                )
            )

            conn.commit()

    def _load_active_events(
        self,
        index_name=None
    ):
        query = """
            SELECT event_type
            FROM distribution_events
            WHERE active = 1
        """

        params = []

        if index_name:

            query += """
                AND index_name = ?
            """

            params.append(
                index_name
            )

        with self._connect() as conn:

            rows = conn.execute(
                query,
                params
            ).fetchall()

        return [
            row[0]
            for row in rows
        ]

    def run(
        self,
        distribution_data
    ):
        """
        Execute distribution analysis.

        Input:

        {
            "index":"SP500",
            "price_change":-1.2,
            "volume_change":18
        }

        Output:

        {
            "distribution_days":3,
            "stall_days":1,
            "churning_days":2,
            "institutional_pressure":42
        }
        """

        logger.info(
            "Running Distribution Analysis"
        )

        if not isinstance(
            distribution_data,
            dict
        ):
            return {}

        index_name = distribution_data.get(
            "index",
            "MARKET"
        )

        distribution_days = 0
        stall_days = 0
        churning_days = 0

        events = distribution_data.get(
            "events",
            []
        )

        if not isinstance(
            events,
            list
        ):
            events = [
                distribution_data
            ]

        for event in events:

            severity = self._calculate_severity(
                event
            )

            if self._detect_distribution_day(
                event
            ):

                distribution_days += 1

                self._save_event(
                    index_name,
                    "DISTRIBUTION",
                    event,
                    severity
                )

            elif self._detect_stall_day(
                event
            ):

                stall_days += 1

                self._save_event(
                    index_name,
                    "STALL",
                    event,
                    severity
                )

            elif self._detect_churning(
                event
            ):

                churning_days += 1

                self._save_event(
                    index_name,
                    "CHURNING",
                    event,
                    severity
                )

        institutional_pressure = min(
            (
                distribution_days * 15
                +
                stall_days * 10
                +
                churning_days * 10
            ),
            100
        )

        return {

            "distribution_days": distribution_days,

            "stall_days": stall_days,

            "churning_days": churning_days,

            "institutional_pressure": institutional_pressure,

            "active_events": self._load_active_events(
                index_name
            ),

            "timestamp": datetime.utcnow().isoformat()

        }
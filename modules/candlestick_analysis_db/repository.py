import sqlite3
from datetime import datetime
from modules.path_resolver import get_candlestick_analysis_db_path


DB_PATH = get_candlestick_analysis_db_path()


class CandlestickRepository:

    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH)
        self.cursor = self.conn.cursor()

    # =====================================================
    # PATTERN EVENTS
    # =====================================================
    def insert_pattern_event(self, ticker, timeframe, timestamp, pattern, direction, ohlcv, state, score):

        self.cursor.execute("""
        INSERT INTO pattern_events (
            ticker, timeframe, timestamp,
            pattern, direction,
            open, high, low, close, volume,
            pattern_state, pattern_score,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            ticker,
            timeframe,
            timestamp,
            pattern,
            direction,
            ohlcv.get("open"),
            ohlcv.get("high"),
            ohlcv.get("low"),
            ohlcv.get("close"),
            ohlcv.get("volume"),
            state,
            score,
            datetime.utcnow().isoformat()
        ))

        self.conn.commit()

    # =====================================================
    # TRADE SETUPS
    # =====================================================
    def insert_trade_setup(self, ticker, timeframe, timestamp, pattern, setup):

        self.cursor.execute("""
        INSERT INTO trade_setups (
            ticker, timeframe, timestamp,
            pattern, bias,
            entry, stop, target,
            entry_price, stop_price, target_price,
            context,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            ticker,
            timeframe,
            timestamp,
            pattern,
            setup.get("bias"),
            setup.get("entry"),
            setup.get("stop"),
            setup.get("target"),
            setup.get("entry_price_hint"),
            setup.get("stop_price_hint"),
            None,
            setup.get("context"),
            datetime.utcnow().isoformat()
        ))

        self.conn.commit()

    # =====================================================
    # CONFIRMATION RESULTS
    # =====================================================
    def insert_result(self, ticker, timeframe, timestamp, pattern, state, score, direction, confirmed, failed, next_close, follow_through):

        self.cursor.execute("""
        INSERT INTO pattern_results (
            ticker, timeframe, timestamp,
            pattern, state, score, direction,
            confirmed, failed,
            next_close, follow_through,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            ticker,
            timeframe,
            timestamp,
            pattern,
            state,
            score,
            direction,
            int(confirmed),
            int(failed),
            next_close,
            follow_through,
            datetime.utcnow().isoformat()
        ))

        self.conn.commit()

    # =====================================================
    # MTF ALIGNMENT
    # =====================================================
    def insert_alignment(self, ticker, timestamp, alignment, results):

        self.cursor.execute("""
        INSERT INTO mtf_alignment (
            ticker, timestamp, alignment,
            tf_15m_pattern, tf_1h_pattern, tf_daily_pattern,
            tf_15m_score, tf_1h_score, tf_daily_score,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            ticker,
            timestamp,
            alignment,

            results["15M"].get("latest_pattern"),
            results["1H"].get("latest_pattern"),
            results["DAILY"].get("latest_pattern"),

            results["15M"].get("pattern_score"),
            results["1H"].get("pattern_score"),
            results["DAILY"].get("pattern_score"),

            datetime.utcnow().isoformat()
        ))

        self.conn.commit()

    # =====================================================
    # STOP LOG
    # =====================================================
    def insert_stop_eval(self, ticker, timeframe, timestamp, pattern, direction, stop_result, stop_price):

        self.cursor.execute("""
        INSERT INTO stop_evaluations (
            ticker, timeframe, timestamp,
            pattern, direction,
            stop_price, status, breached,
            breach_index, reason,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            ticker,
            timeframe,
            timestamp,
            pattern,
            direction,
            stop_price,
            stop_result.get("stop_status"),
            int(stop_result.get("breached")),
            stop_result.get("breach_index"),
            stop_result.get("reason"),
            datetime.utcnow().isoformat()
        ))

        self.conn.commit()

    def close(self):
        self.conn.close()
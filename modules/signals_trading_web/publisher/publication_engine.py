import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from modules.path_resolver import get_trades_db_path
from .database_reader import DatabaseReader
from .public_schema import sanitize_trade


class PublicationEngine:
    def __init__(self, output_dir):
        self.output_dir = Path(output_dir)

        self.output_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        self.trades_db_path = get_trades_db_path()

        self.reader = DatabaseReader(
            self.trades_db_path
        )

        self.analysis_source = (
            ROOT
            / "modules"
            / "signals_trading_web"
            / "data"
            / "analysis_latest.json"
        )

    def _write(self, filename, payload):
        path = self.output_dir / filename

        path.write_text(
            json.dumps(
                payload,
                indent=2,
                ensure_ascii=False
            ),
            encoding="utf-8"
        )

        return path

    def _publish_analysis_latest(self):
        """
        Publish the already-generated authoritative
        analysis_latest.json dataset.

        The signal analysis engine is responsible for
        generating this file.

        The publication engine only validates and publishes
        the existing dataset. It does not regenerate analysis.
        """

        source = self.analysis_source
        destination = (
            self.output_dir
            / "analysis_latest.json"
        )

        if not source.exists():
            return None

        try:
            payload = json.loads(
                source.read_text(
                    encoding="utf-8"
                )
            )

        except (
            json.JSONDecodeError,
            OSError
        ):
            return None

        if not isinstance(
            payload,
            dict
        ):
            return None

        tickers = payload.get(
            "tickers",
            {}
        )

        if not isinstance(
            tickers,
            dict
        ):
            return None

        self._write(
            "analysis_latest.json",
            payload
        )

        return destination

    def publish(self):
        now = datetime.now(
            timezone.utc
        ).isoformat()

        raw_trades = (
            self.reader.read_trades()
        )

        trades = [
            sanitize_trade(trade)
            for trade in raw_trades
        ]

        self._write(
            "trades.json",
            {
                "generated_at": now,
                "count": len(trades),
                "trades": trades
            }
        )

        closed = [
            trade
            for trade in trades
            if str(
                trade.get(
                    "status",
                    ""
                )
            ).upper() == "CLOSED"
        ]

        wins = [
            trade
            for trade in closed
            if float(
                trade.get(
                    "gain_percent"
                ) or 0
            ) > 0
        ]

        losses = [
            trade
            for trade in closed
            if float(
                trade.get(
                    "gain_percent"
                ) or 0
            ) < 0
        ]

        win_rate = (
            round(
                len(wins)
                / len(closed)
                * 100,
                2
            )
            if closed
            else 0
        )

        performance = {
            "generated_at": now,
            "total_trades": len(closed),
            "winning_trades": len(wins),
            "losing_trades": len(losses),
            "win_rate": win_rate,
            "net_r": 0,
            "average_r": 0,
            "profit_factor": 0,
            "max_drawdown_percent": 0
        }

        self._write(
            "performance.json",
            performance
        )

        self._write(
            "market.json",
            {
                "generated_at": now,
                "regime": "UNKNOWN",
                "indices": {}
            }
        )

        analysis_path = (
            self._publish_analysis_latest()
        )

        return {
            "output_dir": self.output_dir,
            "trades_path": (
                self.output_dir
                / "trades.json"
            ),
            "performance_path": (
                self.output_dir
                / "performance.json"
            ),
            "market_path": (
                self.output_dir
                / "market.json"
            ),
            "analysis_latest_path": (
                analysis_path
            )
        }
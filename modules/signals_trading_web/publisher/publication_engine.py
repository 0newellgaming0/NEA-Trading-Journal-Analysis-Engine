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
from .validator import validate_data


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

        self.analysis_latest_source = (
            ROOT /
            "modules" /
            "signals_trading_web" /
            "data" /
            "analysis_latest.json"
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

    def _publish_existing_analysis(self):
        source = self.analysis_latest_source

        if not source.exists():
            raise FileNotFoundError(
                "analysis_latest.json: "
                f"source file not found: {source}"
            )

        try:
            payload = json.loads(
                source.read_text(
                    encoding="utf-8"
                )
            )
        except json.JSONDecodeError as exc:
            raise ValueError(
                "analysis_latest.json: "
                f"invalid JSON: {exc}"
            ) from exc

        if not isinstance(
            payload,
            dict
        ):
            raise ValueError(
                "analysis_latest.json: "
                "root payload must be an object"
            )

        required = (
            "schema_version",
            "generated_at",
            "tickers",
        )

        missing = [
            key
            for key in required
            if key not in payload
        ]

        if missing:
            raise ValueError(
                "analysis_latest.json: "
                f"missing {missing}"
            )

        if not isinstance(
            payload["tickers"],
            dict
        ):
            raise ValueError(
                "analysis_latest.json: "
                "tickers must be an object"
            )

        for ticker, analysis in (
            payload["tickers"].items()
        ):
            if not isinstance(
                analysis,
                dict
            ):
                raise ValueError(
                    "analysis_latest.json: "
                    f"ticker {ticker} must contain "
                    "an object"
                )

            if "analysis_blocks" not in analysis:
                raise ValueError(
                    "analysis_latest.json: "
                    f"ticker {ticker} is missing "
                    "'analysis_blocks'"
                )

            if not isinstance(
                analysis["analysis_blocks"],
                dict
            ):
                raise ValueError(
                    "analysis_latest.json: "
                    f"ticker {ticker} "
                    "'analysis_blocks' must be "
                    "an object"
                )

        return self._write(
            "analysis_latest.json",
            payload
        )

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
                trade.get("status", "")
            ).upper() == "CLOSED"
        ]

        wins = [
            trade
            for trade in closed
            if float(
                trade.get("gain_percent") or 0
            ) > 0
        ]

        losses = [
            trade
            for trade in closed
            if float(
                trade.get("gain_percent") or 0
            ) < 0
        ]

        win_rate = (
            round(
                len(wins) /
                len(closed) *
                100,
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

        self._publish_existing_analysis()

        validate_data(
            self.output_dir
        )

        return self.output_dir
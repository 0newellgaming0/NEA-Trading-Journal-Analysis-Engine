import json
from pathlib import Path


REQUIRED = {
    "trades.json": [
        "generated_at",
        "count",
        "trades"
    ],
    "performance.json": [
        "generated_at",
        "total_trades",
        "winning_trades",
        "losing_trades",
        "win_rate"
    ],
    "market.json": [
        "generated_at",
        "regime"
    ],
    "analysis_latest.json": [
        "schema_version",
        "generated_at",
        "tickers"
    ]
}


def validate_data(data_dir):
    data_dir = Path(data_dir)

    for filename, keys in REQUIRED.items():
        path = data_dir / filename

        if not path.exists():
            raise FileNotFoundError(
                f"{filename}: file not found"
            )

        try:
            payload = json.loads(
                path.read_text(encoding="utf-8")
            )
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"{filename}: invalid JSON: {exc}"
            ) from exc

        if not isinstance(payload, dict):
            raise ValueError(
                f"{filename}: root payload must be an object"
            )

        missing = [
            key
            for key in keys
            if key not in payload
        ]

        if missing:
            raise ValueError(
                f"{filename}: missing {missing}"
            )

        if filename == "analysis_latest.json":
            tickers = payload.get("tickers")

            if not isinstance(tickers, dict):
                raise ValueError(
                    "analysis_latest.json: "
                    "tickers must be an object"
                )

            for ticker, analysis in tickers.items():
                if not isinstance(ticker, str):
                    raise ValueError(
                        "analysis_latest.json: "
                        "ticker keys must be strings"
                    )

                if not isinstance(analysis, dict):
                    raise ValueError(
                        f"analysis_latest.json: "
                        f"ticker {ticker} must contain an object"
                    )

                if "analysis_blocks" not in analysis:
                    raise ValueError(
                        f"analysis_latest.json: "
                        f"ticker {ticker} is missing "
                        "'analysis_blocks'"
                    )

                if not isinstance(
                    analysis["analysis_blocks"],
                    dict
                ):
                    raise ValueError(
                        f"analysis_latest.json: "
                        f"ticker {ticker} "
                        "'analysis_blocks' must be an object"
                    )

    return True
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

    return True
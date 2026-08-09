PUBLIC_TRADE_FIELDS = {
    "ticker",
    "direction",
    "setup",
    "regime",
    "timeframe",
    "entry",
    "stop",
    "target",
    "risk_reward",
    "score",
    "current_price",
    "gain_percent",
    "max_gain_percent",
    "max_loss_percent",
    "status",
    "signal_strength",
    "confluence",
    "created_at",
    "updated_at"
}


def _first(row, *names):
    for name in names:
        value = row.get(name)
        if value is not None:
            return value
    return None


def sanitize_trade(row):
    out = {
        "ticker": row.get("ticker"),
        "direction": row.get("direction"),
        "setup": _first(
            row,
            "setup",
            "trade_type"
        ),
        "regime": row.get("regime"),
        "timeframe": row.get("timeframe"),
        "entry": _first(
            row,
            "entry",
            "entry_price"
        ),
        "stop": _first(
            row,
            "stop",
            "stop_loss"
        ),
        "target": _first(
            row,
            "target",
            "target_price",
            "target1"
        ),
        "risk_reward": _first(
            row,
            "risk_reward",
            "risk_reward_ratio",
            "rr"
        ),
        "score": row.get("score"),
        "current_price": row.get("current_price"),
        "gain_percent": row.get("gain_percent"),
        "max_gain_percent": row.get("max_gain_percent"),
        "max_loss_percent": row.get("max_loss_percent"),
        "status": row.get("status"),
        "signal_strength": _first(
            row,
            "signal_strength",
            "strength"
        ),
        "confluence": row.get("confluence"),
        "created_at": _first(
            row,
            "created_at",
            "entry_time"
        ),
        "updated_at": _first(
            row,
            "updated_at",
            "last_update"
        )
    }

    return {
        field: out[field]
        for field in PUBLIC_TRADE_FIELDS
        if out.get(field) is not None
    }
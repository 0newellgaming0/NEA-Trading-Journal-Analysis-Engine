def calculate_risk(
    account_equity,
    entry,
    stop,
    target,
    quantity,
):
    account_equity = float(account_equity)
    entry = float(entry)
    stop = float(stop)
    target = float(target)
    quantity = int(quantity)

    if account_equity <= 0:
        raise ValueError(
            "account_equity must be greater than 0."
        )

    if entry <= 0:
        raise ValueError(
            "entry must be greater than 0."
        )

    if stop <= 0:
        raise ValueError(
            "stop must be greater than 0."
        )

    if target <= 0:
        raise ValueError(
            "target must be greater than 0."
        )

    if quantity <= 0:
        raise ValueError(
            "quantity must be greater than 0."
        )

    risk_per_share = abs(
        entry - stop
    )

    reward_per_share = abs(
        target - entry
    )

    total_risk = (
        risk_per_share
        * quantity
    )

    total_reward = (
        reward_per_share
        * quantity
    )

    if total_risk <= 0:
        risk_reward = 0.0
    else:
        risk_reward = (
            total_reward
            / total_risk
        )

    risk_percent = (
        total_risk
        / account_equity
    ) * 100.0

    return {
        "account_equity": account_equity,
        "entry": entry,
        "stop": stop,
        "target": target,
        "quantity": quantity,
        "risk_per_share": risk_per_share,
        "reward_per_share": reward_per_share,
        "total_risk": total_risk,
        "total_reward": total_reward,
        "risk_reward": risk_reward,
        "risk_percent": risk_percent,
    }
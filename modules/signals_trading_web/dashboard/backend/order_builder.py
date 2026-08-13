import uuid


# ============================================================
# VALIDATION
# ============================================================

def _normalize_side(side):
    side = str(side).strip().upper()

    if side not in {"BUY", "SELL"}:
        raise ValueError(
            "Order side must be BUY or SELL."
        )

    return side


def _validate_common(
    ticker,
    quantity,
    entry,
    stop_loss,
    take_profit,
):
    ticker = str(ticker).strip().upper()

    if not ticker:
        raise ValueError(
            "Ticker is required."
        )

    quantity = int(quantity)

    if quantity <= 0:
        raise ValueError(
            "Quantity must be greater than zero."
        )

    entry = float(entry)
    stop_loss = float(stop_loss)
    take_profit = float(take_profit)

    if entry <= 0:
        raise ValueError(
            "Entry price must be greater than zero."
        )

    if stop_loss <= 0:
        raise ValueError(
            "Stop loss must be greater than zero."
        )

    if take_profit <= 0:
        raise ValueError(
            "Take profit must be greater than zero."
        )

    return (
        ticker,
        quantity,
        entry,
        stop_loss,
        take_profit,
    )


# ============================================================
# ENTRY ORDER
# ============================================================

def build_entry_order(
    ticker,
    side,
    quantity,
    entry,
    time_in_force="DAY",
    support_trading_session="CORE",
):
    """
    Build a standard Webull v3 equity entry order.

    This function does not submit the order.
    """

    side = _normalize_side(side)

    ticker = str(
        ticker
    ).strip().upper()

    quantity = int(quantity)
    entry = float(entry)

    if not ticker:
        raise ValueError(
            "Ticker is required."
        )

    if quantity <= 0:
        raise ValueError(
            "Quantity must be greater than zero."
        )

    if entry <= 0:
        raise ValueError(
            "Entry price must be greater than zero."
        )

    client_order_id = (
        uuid.uuid4().hex
    )

    return {
        "combo_type": "NORMAL",

        "client_order_id":
            client_order_id,

        "symbol":
            ticker,

        "instrument_type":
            "EQUITY",

        "market":
            "US",

        "order_type":
            "LIMIT",

        "limit_price":
            f"{entry:.4f}",

        "quantity":
            str(quantity),

        "side":
            side,

        "time_in_force":
            str(
                time_in_force
            ).strip().upper(),

        "support_trading_session":
            str(
                support_trading_session
            ).strip().upper(),

        "entrust_type":
            "QTY",
    }


# ============================================================
# PROTECTIVE COMBO
# ============================================================

def build_protective_combo(
    ticker,
    side,
    quantity,
    entry,
    stop_loss,
    take_profit,
    entry_time_in_force="DAY",
    exit_time_in_force="GTC",
):
    """
    Build a Webull OTOCO-style protective order structure.

    Structure:

        MASTER
          |
          +---- STOP_LOSS
          |
          +---- STOP_PROFIT

    The MASTER is the entry order.

    Once the MASTER fills, the protective exit
    orders become active.

    When one protective exit executes, the
    other protective exit is cancelled by
    the broker's combo/OCO mechanism.

    This function only constructs the payload.
    It does not communicate with Webull.
    """

    side = _normalize_side(side)

    (
        ticker,
        quantity,
        entry,
        stop_loss,
        take_profit,
    ) = _validate_common(
        ticker,
        quantity,
        entry,
        stop_loss,
        take_profit,
    )

    # --------------------------------------------------------
    # LONG
    # --------------------------------------------------------

    if side == "BUY":

        if stop_loss >= entry:
            raise ValueError(
                "For a BUY order, stop loss "
                "must be below entry."
            )

        if take_profit <= entry:
            raise ValueError(
                "For a BUY order, take profit "
                "must be above entry."
            )

        exit_side = "SELL"

    # --------------------------------------------------------
    # SHORT
    # --------------------------------------------------------

    else:

        if stop_loss <= entry:
            raise ValueError(
                "For a SELL order, stop loss "
                "must be above entry."
            )

        if take_profit >= entry:
            raise ValueError(
                "For a SELL order, take profit "
                "must be below entry."
            )

        exit_side = "BUY"

    client_combo_order_id = (
        uuid.uuid4().hex
    )

    master_serial_id = (
        uuid.uuid4().hex
    )

    stop_serial_id = (
        uuid.uuid4().hex
    )

    profit_serial_id = (
        uuid.uuid4().hex
    )

    # ========================================================
    # MASTER ENTRY
    # ========================================================

    master = {
        "orderType":
            "LMT",

        "timeInForce":
            str(
                entry_time_in_force
            ).strip().upper(),

        "quantity":
            quantity,

        "outsideRegularTradingHour":
            False,

        "action":
            side,

        "tickerId":
            None,

        "lmtPrice":
            entry,

        "comboType":
            "MASTER",

        "serialId":
            master_serial_id,
    }

    # ========================================================
    # STOP LOSS
    # ========================================================

    stop = {
        "orderType":
            "STP",

        "timeInForce":
            str(
                exit_time_in_force
            ).strip().upper(),

        "quantity":
            quantity,

        "outsideRegularTradingHour":
            False,

        "action":
            exit_side,

        "tickerId":
            None,

        "auxPrice":
            stop_loss,

        "comboType":
            "STOP_LOSS",

        "serialId":
            stop_serial_id,
    }

    # ========================================================
    # TAKE PROFIT
    # ========================================================

    profit = {
        "orderType":
            "LMT",

        "timeInForce":
            str(
                exit_time_in_force
            ).strip().upper(),

        "quantity":
            quantity,

        "outsideRegularTradingHour":
            False,

        "action":
            exit_side,

        "tickerId":
            None,

        "lmtPrice":
            take_profit,

        "comboType":
            "STOP_PROFIT",

        "serialId":
            profit_serial_id,
    }

    # ========================================================
    # COMBO
    # ========================================================

    return {
        "client_combo_order_id":
            client_combo_order_id,

        "ticker":
            ticker,

        "side":
            side,

        "quantity":
            quantity,

        "entry":
            entry,

        "stop_loss":
            stop_loss,

        "take_profit":
            take_profit,

        "orders": [
            master,
            stop,
            profit,
        ],
    }


# ============================================================
# WEBULL V3 ORDER CONVERSION
# ============================================================

def build_v3_protective_orders(
    ticker,
    side,
    quantity,
    entry,
    stop_loss,
    take_profit,
    ticker_id,
    entry_time_in_force="DAY",
    exit_time_in_force="GTC",
):
    """
    Build the actual Webull v3 order list.

    Webull's SDK separates ticker resolution from
    order construction, so ticker_id is supplied by
    webull_client.py.

    Returns:

        {
            "client_combo_order_id": "...",
            "orders": [...]
        }
    """

    side = _normalize_side(side)

    (
        ticker,
        quantity,
        entry,
        stop_loss,
        take_profit,
    ) = _validate_common(
        ticker,
        quantity,
        entry,
        stop_loss,
        take_profit,
    )

    if side == "BUY":

        if stop_loss >= entry:
            raise ValueError(
                "For a BUY order, stop loss "
                "must be below entry."
            )

        if take_profit <= entry:
            raise ValueError(
                "For a BUY order, take profit "
                "must be above entry."
            )

        exit_side = "SELL"

    else:

        if stop_loss <= entry:
            raise ValueError(
                "For a SELL order, stop loss "
                "must be above entry."
            )

        if take_profit >= entry:
            raise ValueError(
                "For a SELL order, take profit "
                "must be below entry."
            )

        exit_side = "BUY"

    if not ticker_id:
        raise ValueError(
            "Webull ticker ID is required."
        )

    client_combo_order_id = (
        uuid.uuid4().hex
    )

    orders = [
        {
            "orderType":
                "LMT",

            "timeInForce":
                str(
                    entry_time_in_force
                ).strip().upper(),

            "quantity":
                quantity,

            "outsideRegularTradingHour":
                False,

            "action":
                side,

            "tickerId":
                ticker_id,

            "lmtPrice":
                entry,

            "comboType":
                "MASTER",

            "serialId":
                uuid.uuid4().hex,
        },

        {
            "orderType":
                "STP",

            "timeInForce":
                str(
                    exit_time_in_force
                ).strip().upper(),

            "quantity":
                quantity,

            "outsideRegularTradingHour":
                False,

            "action":
                exit_side,

            "tickerId":
                ticker_id,

            "auxPrice":
                stop_loss,

            "comboType":
                "STOP_LOSS",

            "serialId":
                uuid.uuid4().hex,
        },

        {
            "orderType":
                "LMT",

            "timeInForce":
                str(
                    exit_time_in_force
                ).strip().upper(),

            "quantity":
                quantity,

            "outsideRegularTradingHour":
                False,

            "action":
                exit_side,

            "tickerId":
                ticker_id,

            "lmtPrice":
                take_profit,

            "comboType":
                "STOP_PROFIT",

            "serialId":
                uuid.uuid4().hex,
        },
    ]

    return {
        "client_combo_order_id":
            client_combo_order_id,

        "orders":
            orders,
    }
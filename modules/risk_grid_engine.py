import tkinter as tk


# ==========================================================
# VARIABLES
# ==========================================================

ticker = None

account = None
low = None
risk_pct = None
risk_dollar = None

stop = None
last_high = None

ladder_prices = []
ladder_shares = []
ladder_totals = []

total_cost = None
total_shares = None

rr_targets = []

buy_now_price = None
buy_now_shares = None
buy_now_total = None

buy_now_manual = {"value": False}
buy_now_internal_update = {"value": False}

stop_manual = {"value": False}

# ==========================================================
# INITIALIZE TK VARIABLES
# ==========================================================
def initialize_risk_engine(root):

    global ticker, account, low, risk_pct, risk_dollar
    global stop, last_high
    global ladder_prices, ladder_shares, ladder_totals
    global total_cost, total_shares
    global rr_targets
    global buy_now_price, buy_now_shares, buy_now_total

    ticker = tk.StringVar(root, value="")
    account = tk.DoubleVar(root, value=1000)
    low = tk.DoubleVar(root, value=0.92)
    risk_pct = tk.DoubleVar(root, value=0.01)
    risk_dollar = tk.DoubleVar(root)

    stop = tk.DoubleVar(root, value=0.55358)
    last_high = tk.DoubleVar(root, value=2.47)

    ladder_prices = [tk.DoubleVar(root) for _ in range(4)]
    ladder_shares = [tk.DoubleVar(root) for _ in range(4)]
    ladder_totals = [tk.DoubleVar(root) for _ in range(4)]

    total_cost = tk.DoubleVar(root)
    total_shares = tk.DoubleVar(root)

    rr_targets = [tk.DoubleVar(root) for _ in range(4)]

    buy_now_price = tk.DoubleVar(root, value=1.716)
    buy_now_shares = tk.DoubleVar(root)
    buy_now_total = tk.DoubleVar(root)

    # traces
    for v in [account, risk_pct, buy_now_price]:
        v.trace_add("write", recalc)

    low.trace_add("write", auto_calc_stop)
    last_high.trace_add("write", auto_calc_stop)
    ladder_prices[0].trace_add("write", auto_set_buy_now)
    stop.trace_add("write", stop_edited)
    buy_now_price.trace_add("write", buy_now_edited)
    
# ==========================================================
# SAFE FLOAT
# ==========================================================

def safe_float(value, default=0.0):

    try:

        value = str(value).strip()

        if value == "":
            return default

        return float(value)

    except:
        return default


# ==========================================================
# PREVIEW TEXT
# ==========================================================

def preview_text(text, limit=40):

    try:

        text = str(text).replace("\n", " ").strip()

        if len(text) <= limit:
            return text

        return text[:limit] + "..."

    except:
        return ""


def build_preview_row(row):

    preview_row = {}

    for k, v in row.items():

        if k in (
            "trade_notes",
            "analysis_notes",
            "management_notes"
        ):

            preview_row[k] = preview_text(v, limit=25)

        else:

            preview_row[k] = v

    return preview_row


# ==========================================================
# STOP ENGINE
# ==========================================================

def auto_calc_stop(*args):

    try:

        lh_raw = str(
            safe_float(last_high.get())
        ).strip()

        lo_raw = str(
            safe_float(low.get())
        ).strip()

        if lh_raw == "" or lo_raw == "":
            return

        lh = float(lh_raw)
        lo = float(lo_raw)

        if lh <= lo:
            return

        price_range = lh - lo

        shakeout_level = lo - (
            price_range * 0.075238
        )

        range_percent = price_range / lh

        if range_percent < 0.10:

            stop_buffer = (
                price_range * 0.06
            )

        elif range_percent < 0.20:

            stop_buffer = (
                price_range * 0.09
            )

        elif range_percent < 0.35:

            stop_buffer = (
                price_range * 0.12
            )

        else:

            stop_buffer = (
                price_range * 0.18
            )

        calc_stop = (
            shakeout_level - stop_buffer
        )

        max_loss_threshold = lo * 0.65

        if calc_stop < max_loss_threshold:

            calc_stop = max_loss_threshold

        if calc_stop <= 0:

            calc_stop = lo * 0.50

        stop.set(
            round(calc_stop, 4)
        )

        stop_manual["value"] = False

        recalc()

    except ValueError:

        pass

    except Exception as e:

        print(
            "auto_calc_stop error:",
            e
        )


def stop_edited(*args):

    stop_manual["value"] = True

    recalc()


# ==========================================================
# CALCULATION ENGINE
# ==========================================================

def recalc(*args):

    try:

        r_dollar = (
            account.get()
            * risk_pct.get()
        )

        risk_dollar.set(
            round(r_dollar, 2)
        )

        price_range = (
            safe_float(last_high.get())
            - safe_float(low.get())
        )

        fib_levels = [
            0.328,
            0.238,
            0.015,
            -0.075238
        ]

        for i, fib in enumerate(fib_levels):

            val = (
                safe_float(low.get())
                + (price_range * fib)
            )

            if i == 3 and val <= 0:

                val = (
                    safe_float(low.get())
                    * 0.88
                )

            ladder_prices[i].set(
                round(val, 4)
            )

        allocations = [
            0.25,
            0.750,
            0,
            0
        ]

        total_sh = 0
        total_cost_val = 0

        for i in range(4):

            risk_per_share = (
                ladder_prices[i].get()
                - safe_float(stop.get())
            )

            sh = (
                (
                    r_dollar
                    * allocations[i]
                )
                / risk_per_share
                if risk_per_share > 0
                else 0
            )

            ladder_shares[i].set(
                round(sh, 2)
            )

            ladder_totals[i].set(
                round(
                    sh
                    * ladder_prices[i].get(),
                    2
                )
            )

            total_sh += sh

            total_cost_val += (
                sh
                * ladder_prices[i].get()
            )

        total_shares.set(
            round(total_sh, 2)
        )

        total_cost.set(
            round(total_cost_val, 2)
        )

        for i in range(4):

            rr_targets[i].set(
                round(
                    ladder_prices[i].get()
                    + (
                        ladder_prices[i].get()
                        - safe_float(stop.get())
                    ),
                    5
                )
            )

        risk_ps = (
            buy_now_price.get()
            - safe_float(stop.get())
        )

        bn_sh = (
            r_dollar / risk_ps
            if risk_ps > 0
            else 0
        )

        buy_now_shares.set(
            round(bn_sh, 2)
        )

        buy_now_total.set(
            round(
                bn_sh
                * buy_now_price.get(),
                4
            )
        )

    except Exception as e:

        print(
            "recalc error:",
            e
        )


def auto_set_buy_now(*args):

    if not buy_now_manual["value"]:

        try:

            buy_now_internal_update["value"] = True

            buy_now_price.set(
                round(
                    ladder_prices[0].get(),
                    4
                )
            )

            buy_now_internal_update["value"] = False

        except:

            buy_now_internal_update["value"] = False


def buy_now_edited(*args):

    if buy_now_internal_update["value"]:
        return

    buy_now_manual["value"] = True

# ==========================================================
# EXTERNAL JOURNAL INTEGRATION HELPERS (ADDED ONLY)
# ==========================================================

def get_engine_state():
    """
    Returns full risk engine state for journal.py sync.
    """
    return {
        "ticker": ticker.get() if ticker else "",
        "account": account.get() if account else 0,
        "low": low.get() if low else 0,
        "risk_pct": risk_pct.get() if risk_pct else 0,
        "risk_dollar": risk_dollar.get() if risk_dollar else 0,
        "stop": stop.get() if stop else 0,
        "last_high": last_high.get() if last_high else 0,
        "ladder_prices": [v.get() for v in ladder_prices],
        "ladder_shares": [v.get() for v in ladder_shares],
        "ladder_totals": [v.get() for v in ladder_totals],
        "total_cost": total_cost.get() if total_cost else 0,
        "total_shares": total_shares.get() if total_shares else 0,
        "rr_targets": [v.get() for v in rr_targets],
        "buy_now_price": buy_now_price.get() if buy_now_price else 0,
        "buy_now_shares": buy_now_shares.get() if buy_now_shares else 0,
        "buy_now_total": buy_now_total.get() if buy_now_total else 0
    }


def set_engine_state(state: dict):
    """
    Syncs journal entry → risk engine (used when opening editor)
    """
    try:
        if not state:
            return

        if ticker and "ticker" in state:
            ticker.set(state["ticker"])

        if account and "account" in state:
            account.set(state["account"])

        if low and "low" in state:
            low.set(state["low"])

        if risk_pct and "risk_pct" in state:
            risk_pct.set(state["risk_pct"])

        if risk_dollar and "risk_dollar" in state:
            risk_dollar.set(state["risk_dollar"])

        if stop and "stop" in state:
            stop.set(state["stop"])

        if last_high and "last_high" in state:
            last_high.set(state["last_high"])

        if "ladder_prices" in state:
            for i, v in enumerate(state["ladder_prices"]):
                if i < len(ladder_prices):
                    ladder_prices[i].set(v)

        if "ladder_shares" in state:
            for i, v in enumerate(state["ladder_shares"]):
                if i < len(ladder_shares):
                    ladder_shares[i].set(v)

        if "ladder_totals" in state:
            for i, v in enumerate(state["ladder_totals"]):
                if i < len(ladder_totals):
                    ladder_totals[i].set(v)

        if total_cost and "total_cost" in state:
            total_cost.set(state["total_cost"])

        if total_shares and "total_shares" in state:
            total_shares.set(state["total_shares"])

        if "rr_targets" in state:
            for i, v in enumerate(state["rr_targets"]):
                if i < len(rr_targets):
                    rr_targets[i].set(v)

        if buy_now_price and "buy_now_price" in state:
            buy_now_price.set(state["buy_now_price"])

        if buy_now_shares and "buy_now_shares" in state:
            buy_now_shares.set(state["buy_now_shares"])

        if buy_now_total and "buy_now_total" in state:
            buy_now_total.set(state["buy_now_total"])

        # force recalculation after sync
        recalc()

    except Exception as e:
        print("set_engine_state error:", e)


def reset_engine():
    """
    Clears risk engine state (useful for new ticker selection)
    """
    try:
        if ticker: ticker.set("")
        if account: account.set(1000)
        if low: low.set(0.92)
        if risk_pct: risk_pct.set(0.01)
        if risk_dollar: risk_dollar.set(0)

        if stop: stop.set(0.55358)
        if last_high: last_high.set(2.47)

        for v in ladder_prices:
            v.set(0)

        for v in ladder_shares:
            v.set(0)

        for v in ladder_totals:
            v.set(0)

        if total_cost: total_cost.set(0)
        if total_shares: total_shares.set(0)

        for v in rr_targets:
            v.set(0)

        if buy_now_price: buy_now_price.set(1.716)
        if buy_now_shares: buy_now_shares.set(0)
        if buy_now_total: buy_now_total.set(0)

        buy_now_manual["value"] = False
        buy_now_internal_update["value"] = False
        stop_manual["value"] = False

    except Exception as e:
        print("reset_engine error:", e)
        
# ==========================================================
# SAFE INITIALIZATION GUARD (ADDED)
# ==========================================================

_engine_initialized = False


def ensure_initialized():
    """
    Prevents journal.py from calling engine before initialize_risk_engine().
    """
    global _engine_initialized

    if not _engine_initialized:
        initialize_risk_engine()
        _engine_initialized = True


def safe_recalc(*args):
    """
    Wrapper used by journal UI to avoid NoneType crashes
    before initialization.
    """
    try:
        ensure_initialized()
        recalc()
    except Exception as e:
        print("safe_recalc error:", e)        
        
        
__all__ = ["initialize_risk_engine"]        
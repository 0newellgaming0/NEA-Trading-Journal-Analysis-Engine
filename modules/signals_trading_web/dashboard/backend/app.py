import logging
import os

from flask import Flask, jsonify, request
from flask_cors import CORS

from config import (
    ALLOW_LIVE_TRADING,
    MIN_RISK_REWARD,
    RISK_PERCENT,
    WEBULL_APP_KEY,
    WEBULL_APP_SECRET,
    WEBULL_ACCESS_TOKEN,
)

from webull_client import WebullClient

from risk_engine import calculate_risk

from order_builder import (
    build_entry_order,
    build_protective_combo,
)


# ============================================================
# APPLICATION
# ============================================================

app = Flask(__name__)

CORS(
    app,
    resources={
        r"/api/*": {
            "origins": [
                "http://127.0.0.1:8080",
                "http://localhost:8080"
            ]
        }
    }
)

log = logging.getLogger(
    "PrivateWebullBackend"
)


# ============================================================
# WEBULL CLIENT
# ============================================================

_webull_client = None


def get_webull_client():
    global _webull_client

    if _webull_client is None:
        _webull_client = WebullClient()

    return _webull_client


# ============================================================
# ERROR HANDLING
# ============================================================

def error_response(exc):
    log.exception(
        "Private Webull backend error"
    )

    return jsonify({
        "error": str(exc)
    }), 500


# ============================================================
# ACCOUNT
# ============================================================

@app.get("/api/account")
def account():
    try:
        client = get_webull_client()

        return jsonify({
            "accounts":
                client.get_accounts()
        })

    except Exception as exc:
        return error_response(exc)


@app.get("/api/account/balance")
def account_balance():
    try:
        client = get_webull_client()

        return jsonify(
            client.get_balance()
        )

    except Exception as exc:
        return error_response(exc)


@app.get("/api/account/positions")
def account_positions():
    try:
        client = get_webull_client()

        return jsonify(
            client.get_positions()
        )

    except Exception as exc:
        return error_response(exc)


# ============================================================
# ORDERS
# ============================================================

@app.get("/api/orders/open")
def open_orders():
    try:
        client = get_webull_client()

        return jsonify(
            client.get_open_orders()
        )

    except Exception as exc:
        return error_response(exc)


# ============================================================
# RISK
# ============================================================

@app.post("/api/trade/risk")
def trade_risk():
    try:
        data = request.get_json(
            silent=True
        ) or {}

        account_equity = float(
            data["account_equity"]
        )

        entry = float(
            data["entry"]
        )

        stop_loss = float(
            data["stop_loss"]
        )

        take_profit = float(
            data["take_profit"]
        )

        quantity = int(
            data["quantity"]
        )

        result = calculate_risk(
            account_equity=account_equity,
            entry=entry,
            stop=stop_loss,
            target=take_profit,
            quantity=quantity,
        )

        result["allowed"] = (
            result["risk_reward"]
            >= MIN_RISK_REWARD
        )

        result["risk_limit"] = (
            account_equity
            * (RISK_PERCENT / 100.0)
        )

        return jsonify(result)

    except KeyError as exc:
        return jsonify({
            "error": (
                f"Missing required field: "
                f"{exc.args[0]}"
            )
        }), 400

    except ValueError as exc:
        return jsonify({
            "error": str(exc)
        }), 400

    except Exception as exc:
        return error_response(exc)


# ============================================================
# ORDER PREVIEW
# ============================================================

@app.post("/api/orders/preview")
def preview_order():
    try:
        data = request.get_json(
            silent=True
        ) or {}

        ticker = str(
            data["ticker"]
        ).strip().upper()

        side = str(
            data["side"]
        ).strip().upper()

        quantity = int(
            data["quantity"]
        )

        entry = float(
            data["entry"]
        )

        stop_loss = float(
            data["stop_loss"]
        )

        take_profit = float(
            data["take_profit"]
        )

        account_equity = float(
            data["account_equity"]
        )

        risk = calculate_risk(
            account_equity=account_equity,
            entry=entry,
            stop=stop_loss,
            target=take_profit,
            quantity=quantity,
        )

        if risk["risk_reward"] < MIN_RISK_REWARD:
            return jsonify({
                "approved": False,
                "error": (
                    "Risk/reward is below "
                    f"1:{MIN_RISK_REWARD:.0f}."
                ),
                "risk": risk,
            }), 400

        entry_order = build_entry_order(
            ticker=ticker,
            side=side,
            quantity=quantity,
            entry=entry,
        )

        client = get_webull_client()

        preview = client.preview_order(
            entry_order
        )

        return jsonify({
            "approved": True,
            "ticker": ticker,
            "side": side,
            "quantity": quantity,
            "entry": entry,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "risk": risk,
            "entry_order": entry_order,
            "webull_preview": preview,
        })

    except KeyError as exc:
        return jsonify({
            "error": (
                f"Missing required field: "
                f"{exc.args[0]}"
            )
        }), 400

    except ValueError as exc:
        return jsonify({
            "error": str(exc)
        }), 400

    except Exception as exc:
        return error_response(exc)


# ============================================================
# PROTECTIVE ORDER PREVIEW
# ============================================================

@app.post("/api/orders/preview-protective")
def preview_protective_order():
    try:
        data = request.get_json(
            silent=True
        ) or {}

        ticker = str(
            data["ticker"]
        ).strip().upper()

        side = str(
            data["side"]
        ).strip().upper()

        quantity = int(
            data["quantity"]
        )

        entry = float(
            data["entry"]
        )

        stop_loss = float(
            data["stop_loss"]
        )

        take_profit = float(
            data["take_profit"]
        )

        account_equity = float(
            data["account_equity"]
        )

        risk = calculate_risk(
            account_equity=account_equity,
            entry=entry,
            stop=stop_loss,
            target=take_profit,
            quantity=quantity,
        )

        if risk["risk_reward"] < MIN_RISK_REWARD:
            return jsonify({
                "approved": False,
                "error": (
                    "Risk/reward is below "
                    f"1:{MIN_RISK_REWARD:.0f}."
                ),
                "risk": risk,
            }), 400

        combo = build_protective_combo(
            ticker=ticker,
            side=side,
            quantity=quantity,
            entry=entry,
            stop_loss=stop_loss,
            take_profit=take_profit,
        )

        client = get_webull_client()

        preview = client.preview_protective_order(
            ticker=ticker,
            side=side,
            quantity=quantity,
            entry=entry,
            stop_loss=stop_loss,
            take_profit=take_profit,
        )

        return jsonify({
            "approved": True,
            "ticker": ticker,
            "side": side,
            "quantity": quantity,
            "entry": entry,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "risk": risk,
            "protective_combo": combo,
            "webull_preview": preview,
        })

    except KeyError as exc:
        return jsonify({
            "error": (
                f"Missing required field: "
                f"{exc.args[0]}"
            )
        }), 400

    except ValueError as exc:
        return jsonify({
            "error": str(exc)
        }), 400

    except Exception as exc:
        return error_response(exc)


# ============================================================
# PLACE PROTECTIVE ORDER
# ============================================================

@app.post("/api/orders/place")
def place_order():
    try:
        if not ALLOW_LIVE_TRADING:
            return jsonify({
                "success": False,
                "error": (
                    "Live trading is disabled. "
                    "Set "
                    "ALLOW_LIVE_TRADING=true "
                    "to enable live order placement."
                ),
            }), 403

        data = request.get_json(
            silent=True
        ) or {}

        ticker = str(
            data["ticker"]
        ).strip().upper()

        side = str(
            data["side"]
        ).strip().upper()

        quantity = int(
            data["quantity"]
        )

        entry = float(
            data["entry"]
        )

        stop_loss = float(
            data["stop_loss"]
        )

        take_profit = float(
            data["take_profit"]
        )

        account_equity = float(
            data["account_equity"]
        )

        risk = calculate_risk(
            account_equity=account_equity,
            entry=entry,
            stop=stop_loss,
            target=take_profit,
            quantity=quantity,
        )

        if risk["risk_reward"] < MIN_RISK_REWARD:
            return jsonify({
                "success": False,
                "error": (
                    "Order rejected because "
                    "risk/reward is below "
                    f"1:{MIN_RISK_REWARD:.0f}."
                ),
                "risk": risk,
            }), 400

        protective_combo = build_protective_combo(
            ticker=ticker,
            side=side,
            quantity=quantity,
            entry=entry,
            stop_loss=stop_loss,
            take_profit=take_profit,
        )

        client = get_webull_client()

        result = client.place_protective_order(
            ticker=ticker,
            side=side,
            quantity=quantity,
            entry=entry,
            stop_loss=stop_loss,
            take_profit=take_profit,
        )

        log.info(
            "LIVE PROTECTIVE ORDER PLACED "
            "ticker=%s side=%s quantity=%s "
            "entry=%s stop=%s target=%s",
            ticker,
            side,
            quantity,
            entry,
            stop_loss,
            take_profit,
        )

        return jsonify({
            "success": True,
            "ticker": ticker,
            "side": side,
            "quantity": quantity,
            "entry": entry,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "risk": risk,
            "protective_combo":
                protective_combo,
            "webull": result,
        })

    except KeyError as exc:
        return jsonify({
            "error": (
                f"Missing required field: "
                f"{exc.args[0]}"
            )
        }), 400

    except ValueError as exc:
        return jsonify({
            "error": str(exc)
        }), 400

    except Exception as exc:
        return error_response(exc)


# ============================================================
# HEALTH
# ============================================================

@app.get("/health")
def health():
    from config import (
        WEBULL_APP_KEY,
        WEBULL_APP_SECRET,
    )

    credentials_configured = bool(
        WEBULL_APP_KEY
        and WEBULL_APP_SECRET
    )

    return jsonify({
        "service":
            "Private Webull Backend",

        "status":
            "ok",

        "webull_credentials":
            credentials_configured,

        "live_trading":
            ALLOW_LIVE_TRADING,

        "risk_percent":
            RISK_PERCENT,

        "minimum_risk_reward":
            MIN_RISK_REWARD,
    })


# ============================================================
# STARTUP
# ============================================================

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format=(
            "%(asctime)s | "
            "%(levelname)s | "
            "%(name)s | "
            "%(message)s"
        ),
    )

    log.info(
        "Starting Private Webull Backend"
    )

    log.info(
        "Live trading enabled: %s",
        ALLOW_LIVE_TRADING
    )

    app.run(
        host=os.environ.get(
            "BACKEND_HOST",
            "127.0.0.1"
        ),
        port=int(
            os.environ.get(
                "BACKEND_PORT",
                "5000"
            )
        ),
        debug=False,
    )
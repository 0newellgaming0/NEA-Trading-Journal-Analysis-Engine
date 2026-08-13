import os


def _env_bool(name, default=False):
    return (
        os.getenv(
            name,
            str(default)
        ).strip().lower()
        == "true"
    )


def _env_float(name, default):
    return float(
        os.getenv(
            name,
            str(default)
        )
    )


def _env_int(name, default):
    return int(
        os.getenv(
            name,
            str(default)
        )
    )


# ============================================================
# WEBULL CONFIGURATION
# ============================================================

WEBULL_APP_KEY = os.getenv(
    "WEBULL_APP_KEY"
)

WEBULL_APP_SECRET = os.getenv(
    "WEBULL_APP_SECRET"
)

WEBULL_ACCESS_TOKEN = os.getenv(
    "WEBULL_ACCESS_TOKEN"
)

WEBULL_ACCOUNT_ID = os.getenv(
    "WEBULL_ACCOUNT_ID"
)

WEBULL_REGION = os.getenv(
    "WEBULL_REGION",
    "us"
)

WEBULL_API_ENDPOINT = os.getenv(
    "WEBULL_API_ENDPOINT",
    "api.webull.com"
)


# ============================================================
# BACKEND CONFIGURATION
# ============================================================

PRIVATE_API_KEY = os.getenv(
    "PRIVATE_API_KEY"
)

BACKEND_HOST = os.getenv(
    "BACKEND_HOST",
    "127.0.0.1"
)

BACKEND_PORT = _env_int(
    "BACKEND_PORT",
    5000
)


# ============================================================
# TRADING SAFETY
# ============================================================

ALLOW_LIVE_TRADING = _env_bool(
    "ALLOW_LIVE_TRADING",
    False
)


# ============================================================
# RISK CONFIGURATION
# ============================================================

RISK_PERCENT = _env_float(
    "RISK_PERCENT",
    0.5
)

MIN_RISK_REWARD = _env_float(
    "MIN_RISK_REWARD",
    2.0
)


# ============================================================
# ORDER CONFIGURATION
# ============================================================

DEFAULT_TIME_IN_FORCE = os.getenv(
    "DEFAULT_TIME_IN_FORCE",
    "DAY"
)

DEFAULT_TRADING_SESSION = os.getenv(
    "DEFAULT_TRADING_SESSION",
    "CORE"
)

DEFAULT_ENTRUST_TYPE = os.getenv(
    "DEFAULT_ENTRUST_TYPE",
    "QTY"
)


# ============================================================
# VALIDATION
# ============================================================

def validate_config():
    missing = []

    if not WEBULL_APP_KEY:
        missing.append(
            "WEBULL_APP_KEY"
        )

    if not WEBULL_APP_SECRET:
        missing.append(
            "WEBULL_APP_SECRET"
        )

    if not WEBULL_ACCESS_TOKEN:
        missing.append(
            "WEBULL_ACCESS_TOKEN"
        )

    if missing:
        raise RuntimeError(
            "Missing Webull environment "
            "credentials: "
            + ", ".join(missing)
        )


def validate_risk_config():
    if RISK_PERCENT <= 0:
        raise ValueError(
            "RISK_PERCENT must be greater than 0."
        )

    if RISK_PERCENT >= 100:
        raise ValueError(
            "RISK_PERCENT must be less than 100."
        )

    if MIN_RISK_REWARD <= 0:
        raise ValueError(
            "MIN_RISK_REWARD must be greater than 0."
        )


# ============================================================
# CONFIGURATION SUMMARY
# ============================================================

def get_config():
    return {
        "webull": {
            "region":
                WEBULL_REGION,

            "endpoint":
                WEBULL_API_ENDPOINT,

            "account_id_configured":
                bool(WEBULL_ACCOUNT_ID),

            "credentials_configured":
                bool(
                    WEBULL_APP_KEY
                    and WEBULL_APP_SECRET
                    and WEBULL_ACCESS_TOKEN
                )
        },

        "backend": {
            "host":
                BACKEND_HOST,

            "port":
                BACKEND_PORT,

            "private_api_key_configured":
                bool(PRIVATE_API_KEY)
        },

        "trading": {
            "live_trading":
                ALLOW_LIVE_TRADING
        },

        "risk": {
            "risk_percent":
                RISK_PERCENT,

            "minimum_risk_reward":
                MIN_RISK_REWARD
        },

        "orders": {
            "default_time_in_force":
                DEFAULT_TIME_IN_FORCE,

            "default_trading_session":
                DEFAULT_TRADING_SESSION,

            "default_entrust_type":
                DEFAULT_ENTRUST_TYPE
        }
    }
import os

def get_project_root():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# =========================================================
# CSV DATA (UNCHANGED)
# =========================================================
def get_stock_data_path(ticker, timeframe="daily"):
    return os.path.join(
        get_project_root(),
        "modules",
        "stock_data",
        timeframe,
        f"{ticker}.csv"
    )

# =========================================================
# FINANCIALS ROOT (SINGLE SOURCE OF TRUTH)
# =========================================================
def get_financials_root():
    return os.path.join(get_project_root(), "modules", "stock_data_db", "financials")

# =========================================================
# DATABASE ROOT (SINGLE SOURCE OF TRUTH)
# =========================================================
def get_database_root():
    return os.path.join(
        get_project_root(),
        "modules",
        "stock_data_db"
    )
    
# =========================================================
# GENERIC DB RESOLVER
# =========================================================
def get_database_path(db_name):
    return os.path.join(get_database_root(), db_name)


# =========================================================
# SPECIFIC DATABASES (CLEAN + CONSISTENT)
# =========================================================
def get_stock_db_path():
    return get_database_path("stock_data.db")


def get_financial_db_path():
    return get_database_path("financials.db")


def get_ingestion_db_path():
    return get_database_path("ingestion.db")


def get_webull_db_path():
    return get_database_path("webull.db")


def get_watchlist_db_path():
    return get_database_path("watchlist.db")


def get_candlestick_analysis_db_path():
    return get_database_path("candlestickAnalysis.db")
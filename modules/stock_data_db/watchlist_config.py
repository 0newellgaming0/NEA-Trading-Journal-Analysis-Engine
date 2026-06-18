import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

WATCHLIST_DB = os.path.join(BASE_DIR, "watchlist.db")

def get_watchlist_db_path():
    return WATCHLIST_DB
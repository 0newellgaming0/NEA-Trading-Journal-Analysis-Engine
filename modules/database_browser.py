import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd

from modules.repositories import (
    StockDataRepository,
    FinancialRepository,
    WatchlistRepository,
    WebullOrdersRepository
)


class DatabaseBrowser:

    def __init__(self, parent):
        self.parent = parent

        # =====================================================
        # USE YOUR EXISTING REPOSITORIES (NO MODIFICATION)
        # =====================================================
        self.stock_repo = StockDataRepository()
        self.fin_repo = FinancialRepository()
        self.watchlist_repo = WatchlistRepository()
        self.webull_repo = WebullOrdersRepository()

    # =====================================================
    # STOCK DATA (FROM REPO ONLY)
    # =====================================================
    def load_stock_data(self, ticker, limit=500):

        self.stock_repo.cursor.execute("""
            SELECT *
            FROM ohlcv_data
            WHERE ticker = ?
            ORDER BY timestamp DESC
            LIMIT ?
        """, (ticker, limit))

        rows = self.stock_repo.cursor.fetchall()

        if not rows:
            return None

        cols = [
            "id", "ticker", "timeframe", "timestamp",
            "open", "high", "low", "close",
            "adj_close", "volume", "created_at"
        ]

        return pd.DataFrame(rows, columns=cols)

    # =====================================================
    # WATCHLIST (REPOSITORY CALL ONLY)
    # =====================================================
    def load_watchlist(self):
        return self.watchlist_repo.get_all()

    # =====================================================
    # WEBULL (REPOSITORY CALL ONLY)
    # =====================================================
    def load_webull_orders(self):
        return self.webull_repo.get_all()

    # =====================================================
    # FINANCIAL DATA (RAW ACCESS VIA REPO CURSOR ONLY)
    # =====================================================
    def load_financials(self):

        self.fin_repo.cursor.execute("""
            SELECT *
            FROM financial_statements
            ORDER BY created_at DESC
        """)

        return self.fin_repo.cursor.fetchall()

    # =====================================================
    # UI
    # =====================================================
    def build(self):

        notebook = ttk.Notebook(self.parent)
        notebook.pack(fill="both", expand=True)

        # ================= SUMMARY =================
        summary_tab = tk.Frame(notebook)
        notebook.add(summary_tab, text="Summary")

        txt = tk.Text(summary_tab)
        txt.pack(fill="both", expand=True)

        txt.insert("end", "DATABASE BROWSER (REPOSITORY ALIGNED)\n\n")

        txt.insert("end", "WATCHLIST:\n")
        for t in self.load_watchlist():
            txt.insert("end", f" - {t}\n")

        txt.insert("end", "\nWEBULL ORDERS:\n")
        for r in self.load_webull_orders():
            txt.insert("end", f" - {r}\n")

        # ================= WEBULL =================
        webull_tab = tk.Frame(notebook)
        notebook.add(webull_tab, text="Webull")

        cols = ("id","Name","Symbol","Side","Status","Filled","Price","Time")
        tree = self._build_table(webull_tab, cols)

        self._load_table(tree, self.load_webull_orders(), cols)

        # ================= STOCK =================
        stock_tab = tk.Frame(notebook)
        notebook.add(stock_tab, text="Stock Data")

        top = tk.Frame(stock_tab)
        top.pack(fill="x")

        ticker_var = tk.StringVar()

        tk.Entry(top, textvariable=ticker_var, width=10).pack(side="left")

        tree_stock = ttk.Treeview(stock_tab, show="headings")
        tree_stock.pack(fill="both", expand=True)

        def load_stock():
            df = self.load_stock_data(ticker_var.get().upper())

            if df is None:
                messagebox.showinfo("Stock", "No data found")
                return

            tree_stock.delete(*tree_stock.get_children())

            tree_stock["columns"] = list(df.columns)

            for c in df.columns:
                tree_stock.heading(c, text=c)

            for _, row in df.iterrows():
                tree_stock.insert("", "end", values=tuple(row))

        tk.Button(top, text="Load", command=load_stock).pack(side="left")

        # ================= FINANCIAL =================
        fin_tab = tk.Frame(notebook)
        notebook.add(fin_tab, text="Financials")

        fin_tree = self._build_table(fin_tab, ("id","ticker","type","data","period","created_at"))
        self._load_table(fin_tree, self.load_financials(), fin_tree["columns"])

    # =====================================================
    # HELPERS
    # =====================================================
    def _build_table(self, parent, columns):

        frame = tk.Frame(parent)
        frame.pack(fill="both", expand=True)

        tree = ttk.Treeview(frame, columns=columns, show="headings")

        for c in columns:
            tree.heading(c, text=c.upper())
            tree.column(c, width=120)

        tree.pack(fill="both", expand=True)

        return tree

    def _load_table(self, tree, data, columns):

        tree.delete(*tree.get_children())

        for row in data:
            if isinstance(row, dict):
                tree.insert("", "end", values=tuple(row.get(c, "") for c in columns))
            else:
                tree.insert("", "end", values=row)
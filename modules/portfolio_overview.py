import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import numpy as np


class PortfolioOverviewPopup:

    # =========================================================
    # INIT
    # =========================================================

    def __init__(self, parent, csv_path=None):

        self.parent = parent
        self.csv_path = csv_path

        self.window = tk.Toplevel(parent)
        self.window.title("Institutional Portfolio Overview (v2)")
        self.window.geometry("1800x950")
        self.window.configure(bg="#111111")

        # CORE DATA LAYERS
        self.raw_df = pd.DataFrame()        # immutable source
        self.df = pd.DataFrame()            # normalized working copy

        # OUTPUT LAYERS
        self.positions_df = pd.DataFrame()
        self.open_df = pd.DataFrame()
        self.closed_df = pd.DataFrame()
        self.pending_df = pd.DataFrame()
        self.timeline_df = pd.DataFrame()

        self.summary = {}

        self.create_ui()

        if csv_path:
            self.load_csv(csv_path)

    # =========================================================
    # UI
    # =========================================================

    def create_ui(self):

        top = tk.Frame(self.window, bg="#111111")
        top.pack(fill="x", padx=10, pady=5)

        tk.Button(top, text="Refresh", command=self.refresh_all,
                  bg="#222", fg="white").pack(side="left", padx=5)

        tk.Button(top, text="Save Working Copy", command=self.save_working_copy,
                  bg="#333", fg="white").pack(side="left", padx=5)

        tk.Button(top, text="Export Positions", command=self.export_positions,
                  bg="#222", fg="white").pack(side="left", padx=5)

        self.search_var = tk.StringVar()

        tk.Label(top, text="Search:", bg="#111111", fg="white").pack(side="right")

        search = tk.Entry(top, textvariable=self.search_var,
                          bg="#222", fg="white", width=35)
        search.pack(side="right", padx=5)
        search.bind("<KeyRelease>", self.filter_tables)

        # NOTEBOOK
        self.nb = ttk.Notebook(self.window)
        self.nb.pack(fill="both", expand=True)

        self.summary_tab = tk.Frame(self.nb, bg="#111111")
        self.open_tab = tk.Frame(self.nb, bg="#111111")
        self.closed_tab = tk.Frame(self.nb, bg="#111111")
        self.pending_tab = tk.Frame(self.nb, bg="#111111")
        self.analytics_tab = tk.Frame(self.nb, bg="#111111")
        self.risk_tab = tk.Frame(self.nb, bg="#111111")
        self.raw_tab = tk.Frame(self.nb, bg="#111111")

        for t, name in [
            (self.summary_tab, "Summary"),
            (self.open_tab, "Open"),
            (self.closed_tab, "Closed"),
            (self.pending_tab, "Pending"),
            (self.analytics_tab, "Analytics"),
            (self.risk_tab, "Risk"),
            (self.raw_tab, "Raw")
        ]:
            self.nb.add(t, text=name)

        self.create_widgets()
        self.create_tables()

    # =========================================================
    # WIDGETS
    # =========================================================

    def create_widgets(self):

        self.summary_text = tk.Text(self.summary_tab, bg="#0f0f0f", fg="#00ff99")
        self.summary_text.pack(fill="both", expand=True)

        self.analytics_text = tk.Text(self.analytics_tab, bg="#0f0f0f", fg="#00ff99")
        self.analytics_text.pack(fill="both", expand=True)

        self.risk_text = tk.Text(self.risk_tab, bg="#0f0f0f", fg="#00ff99")
        self.risk_text.pack(fill="both", expand=True)

    # =========================================================
    # TABLES
    # =========================================================

    def create_tables(self):

        self.open_tree = self.make_tree(self.open_tab)
        self.closed_tree = self.make_tree(self.closed_tab)
        self.pending_tree = self.make_tree(self.pending_tab)
        self.raw_tree = self.make_tree(self.raw_tab)

    def make_tree(self, parent):

        cols = ["Ticker", "Side", "Qty", "Entry", "Exit",
                "PnL", "Status", "Placed", "Filled"]

        tree = ttk.Treeview(parent, columns=cols, show="headings")

        for c in cols:
            tree.heading(c, text=c)
            tree.column(c, width=140, anchor="center")

        tree.pack(fill="both", expand=True)
        return tree

    # =========================================================
    # LOAD + CLEAN
    # =========================================================

    def load_csv(self, path):

        try:
            self.raw_df = pd.read_csv(path)
            self.df = self.raw_df.copy()

            self.clean_data()
            self.build_positions()
            self.calculate_metrics()
            self.populate_all()

        except Exception as e:
            messagebox.showerror("CSV Error", str(e))

    # =========================================================
    # CLEANING (FIXED + STABLE)
    # =========================================================

    def clean_data(self):

        self.df.columns = [c.strip() for c in self.df.columns]

        # normalize ticker column
        if "Symbol" in self.df.columns:
            self.df.rename(columns={"Symbol": "Ticker"}, inplace=True)

        # numeric cleanup
        for c in ["Price", "Avg Price", "Filled", "Total Qty"]:
            if c in self.df.columns:
                self.df[c] = (
                    self.df[c]
                    .astype(str)
                    .str.replace("@", "", regex=False)
                )
                self.df[c] = pd.to_numeric(self.df[c], errors="coerce")

        # datetime cleanup (NO TZ WARNINGS)
        def fix_time(series):
            if series is None:
                return pd.NaT
            return pd.to_datetime(
                series.astype(str)
                .str.replace(" EDT", "", regex=False)
                .str.replace(" EST", "", regex=False)
                .str.strip(),
                errors="coerce"
            )

        if "Placed Time" in self.df:
            self.df["Placed Time"] = fix_time(self.df["Placed Time"])

        if "Filled Time" in self.df:
            self.df["Filled Time"] = fix_time(self.df["Filled Time"])

    # =========================================================
    # CORE RECONSTRUCTION (FIFO FIXED)
    # =========================================================

    def build_positions(self):

        if self.df.empty:
            return

        filled = self.df[self.df["Status"] == "Filled"].copy()
        filled = filled.sort_values("Filled Time")

        results = []

        for ticker in filled["Ticker"].dropna().unique():

            sym = filled[filled["Ticker"] == ticker]

            queue = []
            pnl = 0.0
            trades = 0

            buy_qty = sell_qty = 0

            for _, r in sym.iterrows():

                side = str(r.get("Side", "")).strip()
                qty = float(r.get("Filled", 0) or 0)
                price = float(r.get("Avg Price", 0) or 0)
                t = r.get("Filled Time")

                if side == "Buy":
                    queue.append([qty, price])
                    buy_qty += qty

                elif side == "Sell":
                    sell_qty += qty
                    rem = qty

                    while rem > 0 and queue:

                        bqty, bprice = queue[0]
                        m = min(rem, bqty)

                        pnl += (price - bprice) * m

                        bqty -= m
                        rem -= m

                        trades += 1

                        if bqty == 0:
                            queue.pop(0)
                        else:
                            queue[0][0] = bqty

            open_qty = sum(x[0] for x in queue)

            avg_entry = (
                sum(x[0] * x[1] for x in queue) / open_qty
                if open_qty else 0
            )

            results.append({
                "Ticker": ticker,
                "Buy Qty": buy_qty,
                "Sell Qty": sell_qty,
                "Open Qty": open_qty,
                "Avg Entry": avg_entry,
                "Realized PnL": pnl,
                "Trades": trades,
                "Status": "OPEN" if open_qty else "CLOSED"
            })

        self.positions_df = pd.DataFrame(results)

        self.open_df = self.positions_df[self.positions_df["Open Qty"] > 0]
        self.closed_df = self.positions_df[self.positions_df["Open Qty"] == 0]
        self.pending_df = self.df[self.df["Status"] == "Pending"]

    # =========================================================
    # METRICS
    # =========================================================

    def calculate_metrics(self):

        if self.closed_df.empty:
            self.summary = {"Status": "No closed trades"}
            return

        pnl = self.closed_df["Realized PnL"]

        self.summary = {
            "Total PnL": pnl.sum(),
            "Win Rate": (pnl > 0).mean() * 100,
            "Avg Win": pnl[pnl > 0].mean() if (pnl > 0).any() else 0,
            "Avg Loss": pnl[pnl <= 0].mean() if (pnl <= 0).any() else 0,
            "Trades": len(pnl),
            "Open": len(self.open_df)
        }

    # =========================================================
    # POPULATE UI (FIXED)
    # =========================================================

    def populate_all(self):

        self.populate_summary()
        self.populate_tables()
        self.populate_analytics()
        self.populate_risk()

    def populate_summary(self):

        self.summary_text.delete("1.0", tk.END)

        for k, v in self.summary.items():
            self.summary_text.insert(tk.END, f"{k}: {v}\n")

    def populate_tables(self):

        def fill(tree, df):

            for i in tree.get_children():
                tree.delete(i)

            if df.empty:
                return

            for _, r in df.iterrows():
                tree.insert("", "end", values=(
                    r["Ticker"],
                    "LONG",
                    r.get("Open Qty", r.get("Buy Qty", 0)),
                    r.get("Avg Entry", 0),
                    0,
                    r.get("Realized PnL", 0),
                    r.get("Status", ""),
                    "",
                    ""
                ))

        fill(self.open_tree, self.open_df)
        fill(self.closed_tree, self.closed_df)
        fill(self.pending_tree, self.pending_df)
        fill(self.raw_tree, self.df)

    def populate_analytics(self):

        self.analytics_text.delete("1.0", tk.END)

        if self.positions_df.empty:
            return

        for _, r in self.positions_df.iterrows():

            pnl = r["Realized PnL"]

            label = "Continuation" if pnl > 0 else "Distribution"

            self.analytics_text.insert(
                tk.END,
                f"{r['Ticker']} | {label} | PnL: {pnl} | Trades: {r['Trades']}\n"
            )

    def populate_risk(self):

        self.risk_text.delete("1.0", tk.END)

        exposure = self.positions_df["Buy Qty"].sum()

        self.risk_text.insert(
            tk.END,
            f"Exposure: {exposure}\nOpen: {len(self.open_df)}\nClosed: {len(self.closed_df)}"
        )

    # =========================================================
    # ACTIONS
    # =========================================================

    def refresh_all(self):
        if self.csv_path:
            self.load_csv(self.csv_path)

    def save_working_copy(self):

        path = filedialog.asksaveasfilename(defaultextension=".csv")
        if path:
            self.df.to_csv(path, index=False)

    def export_positions(self):

        path = filedialog.asksaveasfilename(defaultextension=".csv")
        if path:
            self.positions_df.to_csv(path, index=False)

    def filter_tables(self, event=None):

        q = self.search_var.get().lower()

        for tree in [self.open_tree, self.closed_tree, self.pending_tree, self.raw_tree]:

            for item in tree.get_children():

                text = " ".join(map(str, tree.item(item)["values"])).lower()

                if q in text:
                    tree.reattach(item, "", "end")
                else:
                    tree.detach(item)
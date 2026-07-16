import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import json
import pandas as pd

from modules.path_resolver import get_sec_analysis_db_path


# =========================================================
# DB ACCESS
# =========================================================

DB_PATH = get_sec_analysis_db_path()


def load_sec_analysis(filters=None):
    """
    Load SEC analysis results from secAnalysis.db.
    """

    conn = sqlite3.connect(DB_PATH)

    query = """
        SELECT *
        FROM analysis_summary
        WHERE 1=1
    """

    params = []

    if filters:

        ticker = filters.get("ticker")
        if ticker:
            query += " AND ticker LIKE ?"
            params.append(f"%{ticker.upper()}%")

        state = filters.get("state")
        if state:
            query += " AND institutional_sponsorship LIKE ?"
            params.append(f"%{state}%")

        risk = filters.get("risk")
        if risk:
            query += " AND financial_risk LIKE ?"
            params.append(f"%{risk}%")

        classification = filters.get("classification")
        if classification:
            query += " AND classification LIKE ?"
            params.append(f"%{classification}%")
            
        growth_score = filters.get("growth_score")
        if growth_score:
            query += " AND growth_asymmetry_score >= ?"
            params.append(float(growth_score))

        cagr_bonus = filters.get("cagr_bonus")
        if cagr_bonus:
            query += " AND cagr_bonus >= ?"
            params.append(float(cagr_bonus))            

    query += " ORDER BY analysis_date DESC"

    df = pd.read_sql_query(
        query,
        conn,
        params=params
    )

    conn.close()

    return df


def load_json_report(ticker):
    """
    Return the stored JSON report for a ticker.
    """

    conn = sqlite3.connect(DB_PATH)

    cur = conn.cursor()

    cur.execute(
        """
        SELECT json_report
        FROM analysis_summary
        WHERE ticker = ?
        """,
        (ticker.upper(),)
    )

    row = cur.fetchone()

    conn.close()

    if row is None:
        return None

    try:
        return json.loads(row[0])
    except Exception:
        return row[0]

def calculate_cagr_bonus(cagr, metric="revenue"):
    if cagr is None:
        return 0

    if metric == "earnings":
        if cagr >= 30:
            return 25
        elif cagr >= 20:
            return 18
        elif cagr >= 10:
            return 12
        elif cagr >= 5:
            return 5
        return 0

    else:
        if cagr >= 30:
            return 20
        elif cagr >= 20:
            return 15
        elif cagr >= 10:
            return 10
        elif cagr >= 5:
            return 5
        return 2
        
def load_sec_analysis_json(filters=None):
    conn = sqlite3.connect(DB_PATH)

    query = """
        SELECT ticker, analysis_date, json_report
        FROM analysis_summary
        WHERE 1=1
    """
    params = []

    if filters:
        ticker = filters.get("ticker")
        if ticker:
            query += " AND ticker LIKE ?"
            params.append(f"%{ticker.upper()}%")

    query += " ORDER BY analysis_date DESC"

    rows = conn.execute(query, params).fetchall()
    conn.close()

    records = []

    for ticker, date, json_report in rows:
        try:
            report = json.loads(json_report)
        except Exception:
            continue

        ee = report.get("enhanced_earnings", {})
        ag = report.get("annual_growth", {})
        fa = report.get("float_analysis", {})
        ca = report.get("capital_allocation", {})
        cs = report.get("canslim", {})

        revenue = ag.get("revenue", {})
        earnings = ag.get("earnings", {})
        growth = ag.get("growth_quality", {})
        revenue_cagr_bonus = calculate_cagr_bonus(
            revenue.get("cagr3"),
            "revenue"
        )

        earnings_cagr_bonus = calculate_cagr_bonus(
            earnings.get("cagr3"),
            "earnings"
        )

        cagr_bonus = min(
            revenue_cagr_bonus + earnings_cagr_bonus,
            30
        )
        
        revenue_text = []
        if revenue.get("trend"):
            revenue_text.append(revenue.get("trend"))
        if revenue.get("acceleration", {}).get("state"):
            revenue_text.append(revenue.get("acceleration", {}).get("state"))
        if revenue.get("cagr3") is not None:
            revenue_text.append(f"3Y CAGR {revenue['cagr3']:.1f}%")

        earnings_text = []
        if ee.get("trend"):
            earnings_text.append(ee.get("trend"))
        if earnings.get("trend"):
            earnings_text.append(earnings.get("trend"))
        if earnings.get("cagr3") is not None:
            earnings_text.append(f"3Y CAGR {earnings['cagr3']:.1f}%")

        float_text = " | ".join(filter(None, [
            fa.get("float_category"),
            fa.get("float_scarcity"),
            fa.get("dilution_state")
        ]))

        capital_text = " | ".join(filter(None, [
            ca.get("capital_efficiency"),
            ca.get("allocation_sustainability")
        ]))

        canslim_text = " | ".join(filter(None, [
            cs.get("classification"),
            f"Score {cs.get('score')}" if cs.get("score") is not None else None
        ]))

        records.append({
            "ticker": ticker,
            "analysis_date": date,
            "classification": report.get("classification", {}).get("classification"),
            "inst_score": report.get("inst_score"),
            "growth_a_score": (
                (report.get("growth_a_score") or 0)
                + cagr_bonus
            ),
            "cagr_bonus": cagr_bonus,
            "growth_quality": (
                f"{growth.get('rating')}"
                + (f" ({growth.get('score')})" if growth.get("score") is not None else "")
                if growth.get("rating")
                else "UNKNOWN"
            ),
            "revenue": " | ".join(revenue_text),
            "earnings": " | ".join(earnings_text),
            "float": float_text,
            "capital": capital_text,
            "risk": report.get("financial_risk"),
            "liquidity": report.get("liquidity_score"),
            "canslim": canslim_text,
            "institutional": cs.get("institutional")
        })

    return pd.DataFrame(records)
    
# =====================================================
# POPUP
# =====================================================

class SECAnalysisPopup(tk.Toplevel):

    def __init__(self, parent):
        super().__init__(parent)

        self.title("SEC Analysis Database Viewer")
        self.geometry("1500x700")

        self.sort_reverse = False
        self.df = None

        self.columns = [
            "ticker",
            "analysis_date",
            "classification",
            "inst_score",
            "growth_a_score",
            "cagr_bonus",
            "growth_quality",
            "revenue",
            "earnings",
            "float",
            "capital",
            "risk",
            "liquidity",
            "canslim",
            "institutional",
        ]

        self.build_ui()
        self.refresh()

    # =====================================================
    # UI
    # =====================================================

    def build_ui(self):

        header = tk.Frame(self)
        header.pack(fill="x")

        tk.Label(
            header,
            text="SEC ANALYSIS DATABASE",
            font=("Arial", 12, "bold")
        ).pack(side="left", padx=10)

        # -------------------------------------------------
        # FILTERS
        # -------------------------------------------------

        self.filter_ticker = tk.StringVar()
        self.filter_state = tk.StringVar()
        self.filter_risk = tk.StringVar()
        self.filter_classification = tk.StringVar()
        self.filter_growth_score = tk.StringVar()
        self.filter_cagr_bonus = tk.StringVar()

        toolbar = tk.Frame(header)
        toolbar.pack(side="left", padx=10)

        tk.Label(toolbar, text="Ticker").grid(row=0, column=0, padx=3)

        tk.Entry(
            toolbar,
            textvariable=self.filter_ticker,
            width=10
        ).grid(row=0, column=1, padx=3)


        tk.Label(toolbar, text="Classification").grid(row=0, column=2, padx=3)

        tk.Entry(
            toolbar,
            textvariable=self.filter_classification,
            width=18
        ).grid(row=0, column=3, padx=3)


        tk.Label(toolbar, text="Risk").grid(row=0, column=4, padx=3)

        tk.Entry(
            toolbar,
            textvariable=self.filter_risk,
            width=12
        ).grid(row=0, column=5, padx=3)


        tk.Label(toolbar, text="Institutional State").grid(row=0, column=6, padx=3)

        tk.Entry(
            toolbar,
            textvariable=self.filter_state,
            width=18
        ).grid(row=0, column=7, padx=3)


        tk.Label(toolbar, text="Min Growth Score").grid(row=0, column=8, padx=3)

        tk.Entry(
            toolbar,
            textvariable=self.filter_growth_score,
            width=10
        ).grid(row=0, column=9, padx=3)


        tk.Label(toolbar, text="Min CAGR Bonus").grid(row=0, column=10, padx=3)

        tk.Entry(
            toolbar,
            textvariable=self.filter_cagr_bonus,
            width=10
        ).grid(row=0, column=11, padx=3)

        tk.Button(
            header,
            text="FILTER",
            command=self.refresh
        ).pack(side="left", padx=5)

        tk.Button(
            header,
            text="CLEAR",
            command=self.clear_filters
        ).pack(side="left", padx=5)

        tk.Button(
            header,
            text="REFRESH",
            command=self.refresh
        ).pack(side="right", padx=5)

        # -------------------------------------------------
        # TREEVIEW
        # -------------------------------------------------

        self.tree = ttk.Treeview(
            self,
            columns=self.columns,
            show="headings"
        )

        vsb = ttk.Scrollbar(
            self,
            orient="vertical",
            command=self.tree.yview
        )

        hsb = ttk.Scrollbar(
            self,
            orient="horizontal",
            command=self.tree.xview
        )

        self.tree.configure(
            yscrollcommand=vsb.set,
            xscrollcommand=hsb.set
        )

        widths = {
            "ticker": 80,
            "analysis_date": 165,
            "classification": 90,
            "inst_score": 80,
            "growth_a_score": 100,
            "cagr_bonus": 80,
            "growth_quality": 170,
            "revenue": 170,
            "earnings": 140,
            "float": 180,
            "capital": 170,
            "risk": 80,
            "liquidity": 80,
            "canslim": 170,
            "institutional": 140,
        }

        for column in self.columns:

            self.tree.heading(
                column,
                text=column.replace("_", " ").title(),
                command=lambda c=column: self.sort_by(c)
            )

            self.tree.column(
                column,
                width=widths.get(column, 120),
                anchor="center",
                stretch=True
            )

        self.tree.pack(
            fill="both",
            expand=True
        )

        vsb.pack(
            side="right",
            fill="y"
        )

        hsb.pack(
            side="bottom",
            fill="x"
        )

        self.tree.bind(
            "<Double-1>",
            self.show_json_report
        )
        
    # =====================================================
    # LOAD DATA
    # =====================================================

    def refresh(self):

        filters = {
            "ticker": self.filter_ticker.get().strip(),
            "state": self.filter_state.get().strip(),
            "risk": self.filter_risk.get().strip(),
            "classification": self.filter_classification.get().strip(),
            "growth_score": self.filter_growth_score.get().strip(),
            "cagr_bonus": self.filter_cagr_bonus.get().strip()
        }

        # Remove empty filters
        filters = {
            k: v
            for k, v in filters.items()
            if v
        }

        self.df = load_sec_analysis_json(filters)

        self.tree.delete(*self.tree.get_children())

        for _, row in self.df.iterrows():

            values = [
                row.get(column, "")
                for column in self.columns
            ]

            self.tree.insert(
                "",
                "end",
                values=values
            )
        
    # =====================================================
    # SORTING
    # =====================================================

    def sort_by(self, column):

        items = [

            (
                self.tree.set(item, column),
                item

            )

            for item in self.tree.get_children("")

        ]

        def convert(value):

            try:
                return float(value)

            except Exception:
                return str(value).upper()

        items.sort(

            key=lambda x: convert(x[0]),

            reverse=self.sort_reverse

        )

        for index, (_, item) in enumerate(items):

            self.tree.move(

                item,

                "",

                index

            )

        self.sort_reverse = not self.sort_reverse

    # =====================================================
    # JSON REPORT VIEWER
    # =====================================================

    def show_json_report(self, event):

        item = self.tree.identify_row(event.y)

        if not item:
            return

        values = self.tree.item(item, "values")

        if not values:
            return

        ticker = values[0]

        report = load_json_report(ticker)

        if report is None:

            messagebox.showinfo(
                "SEC Analysis",
                f"No JSON report found for {ticker}"
            )

            return

        viewer = tk.Toplevel(self)

        viewer.title(
            f"SEC Analysis Report - {ticker}"
        )

        viewer.geometry("900x700")

        text = tk.Text(
            viewer,
            wrap="none",
            font=("Consolas", 10)
        )

        yscroll = ttk.Scrollbar(
            viewer,
            orient="vertical",
            command=text.yview
        )

        xscroll = ttk.Scrollbar(
            viewer,
            orient="horizontal",
            command=text.xview
        )

        text.configure(

            yscrollcommand=yscroll.set,

            xscrollcommand=xscroll.set

        )

        text.pack(
            side="left",
            fill="both",
            expand=True
        )

        yscroll.pack(
            side="right",
            fill="y"
        )

        xscroll.pack(
            side="bottom",
            fill="x"
        )

        if isinstance(report, dict):

            report = json.dumps(
                report,
                indent=4
            )

        text.insert(
            "1.0",
            report
        )

        text.config(
            state="disabled"
        )

    # =====================================================
    # CLEAR FILTERS
    # =====================================================

    def clear_filters(self):

        self.filter_ticker.set("")

        self.filter_state.set("")

        self.filter_risk.set("")

        self.filter_classification.set("")
        self.filter_growth_score.set("")
        self.filter_cagr_bonus.set("")        

        self.refresh()
        
    def run_full_system_thread(self):
        threading.Thread(
            target=run_full_signal_engine_system,
            daemon=True
        ).start()        
    
    # =====================================================
    # CLOSE
    # =====================================================

    def close(self):
        self.destroy()

    
# =====================================================
# LAUNCHER
# =====================================================

def open_sec_analysis_popup(root):

    SECAnalysisPopup(root)
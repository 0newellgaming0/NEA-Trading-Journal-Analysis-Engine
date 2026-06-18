import tkinter as tk
from tkinter import ttk, messagebox, END
import tkinter.scrolledtext as st
import csv
import os
from pathlib import Path


# ==========================================================
# MAIN MODULE WRAPPER
# ==========================================================
class ExecutedTradeModule:

    def __init__(
        self,
        root,
        trades_table,
        template_text_widget,
        template_ticker_var,

        executed_trades_file,
        executed_trade_note_fields,
        price_like_cols,

        load_webull_executions=None,
        update_template_panel=None,

        # OPTIONAL LEGACY COMPATIBILITY (SAFE BUT NOT REQUIRED)
        notes_file=None,
        note_fields=None,
        notes_loader=None,

        # context blocks
        history_block="",
        daily_volume_block="",
        intraday_block="",
        volume_block="",
        financial_block="",
        historical_results="",
        intraday_15m_prompt="",
        intraday_60m_prompt="",
        pnf_block="",
        fractal_block=""
    ):

        # UI
        self.root = root
        self.trades_table = trades_table
        self.template_text_widget = template_text_widget
        self.template_ticker_var = template_ticker_var

        # Config
        self.EXECUTED_TRADES_NOTES_FILE = Path(executed_trades_file)
        self.EXECUTED_TRADE_NOTE_FIELDS = executed_trade_note_fields
        self.PRICE_LIKE_COLS = price_like_cols

        # External functions
        self.load_webull_executions = load_webull_executions
        self.update_template_panel = update_template_panel

        # Context blocks
        self.history_block = history_block
        self.daily_volume_block = daily_volume_block
        self.intraday_block = intraday_block
        self.volume_block = volume_block
        self.financial_block = financial_block
        self.historical_results = historical_results
        self.intraday_15m_prompt = intraday_15m_prompt
        self.intraday_60m_prompt = intraday_60m_prompt
        self.pnf_block = pnf_block
        self.fractal_block = fractal_block

    # ==========================================================
    # LOAD EXECUTED TRADES
    # ==========================================================
    def load_executed_trades(self):

        trades = self.load_webull_executions()

        self.trades_table.delete(*self.trades_table.get_children())

        if not trades:
            return

        ordered_cols = ["Placed Time"]
        ordered_cols += [
            c for c in trades[0].keys()
            if c not in ("Placed Time", "Status")
        ]

        self.trades_table["columns"] = ordered_cols

        for c in ordered_cols:
            label = "Date" if c == "Placed Time" else c
            self.trades_table.heading(c, text=label)
            self.trades_table.column(c, width=110, anchor="center")

        for r in trades:
            row_vals = []

            for c in ordered_cols:
                val = r.get(c, "")

                if c in self.PRICE_LIKE_COLS:
                    try:
                        val_clean = str(val).replace("@", "").replace(",", "")
                        val = "{:g}".format(float(val_clean))
                    except:
                        pass

                row_vals.append(val)

            self.trades_table.insert("", "end", values=row_vals)

    # ==========================================================
    # LOAD NOTES
    # ==========================================================
    def load_executed_trade_notes(self):

        notes_map = {}

        if not self.EXECUTED_TRADES_NOTES_FILE.exists():
            return notes_map

        with open(self.EXECUTED_TRADES_NOTES_FILE, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)

            for row in reader:
                trade_id = row.get("trade_id", "")
                if trade_id:
                    notes_map[trade_id] = row

        return notes_map

    # ==========================================================
    # CONTEXT REFRESH
    # ==========================================================
    def refresh_executed_trade_context(self, row_data):

        ticker = (row_data.get("Ticker") or row_data.get("Symbol") or "").strip()

        if not ticker:
            return

        try:
            self.template_ticker_var.set(ticker)
            self.update_template_panel()

        except Exception as e:
            print("Executed trade context refresh error:", e)

    # ==========================================================
    # PROMPT GENERATION (INTERNAL ONLY — FIXED)
    # ==========================================================
    def generate_executed_trade_prompt(self, row_data):

        self.refresh_executed_trade_context(row_data)

        template_text = """
You are a seasoned 30 year institutional trader.

Perform a complete institutional-grade post-trade review.

Focus heavily on:
- execution quality
- continuation vs redistribution
- volatility expansion
- institutional accumulation/distribution
- stop placement quality
- entry efficiency
- trade management analysis
- exit efficiency
- scaling logic
- momentum alignment
- T-line continuation structures
- J-hook continuation probability
- RSI 80+
- Elliott Wave context
- Wyckoff phase behavior
- Fibonacci interaction
- risk/reward efficiency
- asymmetry evaluation
- psychology & discipline

====================================================
EXECUTED TRADE DATA
====================================================
"""

        for col in self.trades_table["columns"]:
            value = row_data.get(col, "")

            if col in self.PRICE_LIKE_COLS:
                try:
                    value_clean = str(value).replace("@", "").replace(",", "")
                    value = f"{float(value_clean):g}"
                except:
                    pass

            template_text += f"{col}: {value}\n"

        template_text += f"""

====================================================
DAILY CONTEXT
====================================================

{self.history_block}

====================================================
VOLUME CONTEXT
====================================================

{self.daily_volume_block}

====================================================
INTRADAY CONTEXT
====================================================

{self.intraday_block}

====================================================
VOLUME ANALYSIS
====================================================

{self.volume_block}

====================================================
FINANCIAL METRICS
====================================================

{self.financial_block}

====================================================
PRICE ACTION STRUCTURE
====================================================

{self.historical_results}

{self.intraday_15m_prompt}

{self.intraday_60m_prompt}

====================================================
WYCKOFF / FRACTAL STRUCTURE
====================================================

{self.pnf_block}

{self.fractal_block}
"""

        return template_text

    # ==========================================================
    # SELECTION UPDATE
    # ==========================================================
    def executed_trade_selection_update(self, event=None):

        selected = self.trades_table.selection()
        if not selected:
            return

        item = selected[0]

        row_values = self.trades_table.item(item, "values")

        row_data = {
            col: val
            for col, val in zip(self.trades_table["columns"], row_values)
        }

        template_text = self.generate_executed_trade_prompt(row_data)

        self.template_text_widget.config(state="normal")
        self.template_text_widget.delete("1.0", END)
        self.template_text_widget.insert(END, template_text)
        self.template_text_widget.config(state="disabled")

    # ==========================================================
    # POPUP EDITOR
    # ==========================================================
    def open_executed_trade_editor(self, event=None):

        selected = self.trades_table.selection()
        if not selected:
            return

        item_id = selected[0]
        row_values = self.trades_table.item(item_id, "values")

        row_data = {
            col: val
            for col, val in zip(self.trades_table["columns"], row_values)
        }

        ticker = row_data.get("Ticker") or row_data.get("Symbol") or ""
        placed_time = row_data.get("Placed Time", "")

        trade_id = f"{ticker.strip()}_{placed_time.strip()}"

        notes_map = self.load_executed_trade_notes()
        saved_notes = notes_map.get(trade_id, {})

        template_text = self.generate_executed_trade_prompt(row_data)

        popup = tk.Toplevel(self.root)
        popup.title(f"Executed Trade Review - {ticker}")
        popup.geometry("1100x800")
        popup.configure(bg="#f2f2f2")

        notebook = ttk.Notebook(popup)
        notebook.pack(fill="both", expand=True, padx=5, pady=5)

        notes_tab = tk.Frame(notebook, bg="#f2f2f2")
        analysis_tab = tk.Frame(notebook, bg="#f2f2f2")
        management_tab = tk.Frame(notebook, bg="#f2f2f2")

        notebook.add(notes_tab, text="Notes")
        notebook.add(analysis_tab, text="Analysis")
        notebook.add(management_tab, text="Management")

        notes_text = st.ScrolledText(notes_tab, wrap="word", font=("Courier", 10))
        notes_text.pack(fill="both", expand=True)
        notes_text.insert("1.0", saved_notes.get("notes", ""))

        analysis_text = st.ScrolledText(analysis_tab, wrap="word", font=("Courier", 10))
        analysis_text.pack(fill="both", expand=True)
        analysis_text.insert("1.0", saved_notes.get("analysis_notes", template_text))

        management_text = st.ScrolledText(management_tab, wrap="word", font=("Courier", 10))
        management_text.pack(fill="both", expand=True)
        management_text.insert("1.0", saved_notes.get("management_notes", ""))

        def save():

            rows = []

            if self.EXECUTED_TRADES_NOTES_FILE.exists():
                with open(self.EXECUTED_TRADES_NOTES_FILE, "r", encoding="utf-8") as f:
                    rows = list(csv.DictReader(f))

            updated = False

            for row in rows:
                if row.get("trade_id") == trade_id:
                    row["trade_id"] = trade_id
                    row["notes"] = notes_text.get("1.0", END).strip()
                    row["analysis_notes"] = analysis_text.get("1.0", END).strip()
                    row["management_notes"] = management_text.get("1.0", END).strip()
                    updated = True

            if not updated:
                rows.append({
                    "trade_id": trade_id,
                    "notes": notes_text.get("1.0", END).strip(),
                    "analysis_notes": analysis_text.get("1.0", END).strip(),
                    "management_notes": management_text.get("1.0", END).strip()
                })

            with open(self.EXECUTED_TRADES_NOTES_FILE, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=self.EXECUTED_TRADE_NOTE_FIELDS)
                writer.writeheader()
                writer.writerows(rows)

            messagebox.showinfo("Saved", "Trade updated.")

        bottom = tk.Frame(popup, bg="#f2f2f2")
        bottom.pack(fill="x")

        tk.Button(bottom, text="UPDATE", command=save, bg="#1565c0", fg="white").pack(side="left", padx=10)
        tk.Button(bottom, text="CLOSE", command=popup.destroy, bg="#d32f2f", fg="white").pack(side="right", padx=10)


# ==========================================================
# BIND HELPERS
# ==========================================================
def attach_executed_trade_module(module: ExecutedTradeModule):

    module.trades_table.bind(
        "<<TreeviewSelect>>",
        module.executed_trade_selection_update
    )

    module.trades_table.bind(
        "<Double-1>",
        module.open_executed_trade_editor
    )
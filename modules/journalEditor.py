# ==========================================================
# ADVANCED JOURNAL ENTRY EDITOR (FIXED + SAFE PLUG-IN VERSION)
# ==========================================================

from tkinter import ttk, messagebox, scrolledtext
import tkinter as tk
import csv
import os
from datetime import datetime


def open_entry_editor(
    event=None,
    tree=None,
    root=None,
    journal_rows=None,
    CSV_FIELDS=None,
    JOURNAL_FILE=None,
    load_journal=None,
    delete_journal_entry=None,
    generate_signal_template=None
):

    # ======================================================
    # SAFETY VALIDATION (NO SILENT FAILURES)
    # ======================================================
    if tree is None or root is None or journal_rows is None:
        raise ValueError("[JournalEditor] Missing required UI dependencies")

    selected = tree.selection()
    if not selected:
        return

    item_id = selected[0]
    values = tree.item(item_id, "values")

    if not values or len(values) == 0:
        messagebox.showerror("Error", "Invalid selection.")
        return

    selected_timestamp = values[0]
    entry_timestamp = selected_timestamp

    # ======================================================
    # FIND ROW
    # ======================================================
    row_data = None

    for row in journal_rows:
        if row.get("timestamp") == selected_timestamp:
            row_data = row
            break

    if row_data is None:
        messagebox.showerror("Error", "Unable to locate journal entry.")
        return

    # ======================================================
    # POPUP WINDOW
    # ======================================================
    popup = tk.Toplevel(root)
    popup.title(f"Trade Journal Entry - {row_data.get('ticker','')}")
    popup.geometry("800x650")
    popup.configure(bg="#f2f2f2")

    # ======================================================
    # NOTEBOOK
    # ======================================================
    notebook = ttk.Notebook(popup)
    notebook.pack(fill="both", expand=True, padx=5, pady=5)

    trade_tab = tk.Frame(notebook, bg="#f2f2f2")
    notes_tab = tk.Frame(notebook, bg="#f2f2f2")
    analysis_tab = tk.Frame(notebook, bg="#f2f2f2")
    management_tab = tk.Frame(notebook, bg="#f2f2f2")

    notebook.add(trade_tab, text="Trade")
    notebook.add(notes_tab, text="Notes")
    notebook.add(analysis_tab, text="Analysis")
    notebook.add(management_tab, text="Management")

    # ======================================================
    # TRADE TAB
    # ======================================================
    FIELD_LABELS = {
        "timestamp": "Entry Date",
        "ticker": "Ticker",
        "account": "Account Size",
        "risk_dollar": "Risk Dollar",
        "stop": "Stop Loss",
        "ladder_1_price": "Range High",
        "ladder_2_price": "Range Low",
        "ladder_3_price": "Wave 1 Retracement",
        "ladder_4_price": "Shakeout",
        "buy_now_price": "Buy Now Price",
        "buy_now_shares": "Buy Now Shares",
        "buy_now_total": "Buy Now Total"
    }

    popup_vars = {}
    trade_fields = [
        "ticker", "account", "risk_dollar", "stop",
        "ladder_1_price", "ladder_2_price",
        "ladder_3_price", "ladder_4_price",
        "buy_now_price", "buy_now_shares", "buy_now_total"
    ]

    row_index = 0

    for field in trade_fields:

        tk.Label(
            trade_tab,
            text=FIELD_LABELS.get(field, field),
            font=("Arial", 11, "bold"),
            bg="#f2f2f2"
        ).grid(row=row_index, column=0, sticky="w", padx=10, pady=6)

        var = tk.StringVar(value=row_data.get(field, ""))
        popup_vars[field] = var

        tk.Entry(
            trade_tab,
            textvariable=var,
            font=("Arial", 11),
            width=30
        ).grid(row=row_index, column=1, padx=10, pady=6)

        row_index += 1

    # ======================================================
    # LIVE RECALC (FIXED SAFE VERSION)
    # ======================================================
    def popup_recalc(*args):

        try:
            risk_dollar = float(popup_vars["risk_dollar"].get())
            stop = float(popup_vars["stop"].get())
            buy_now = float(popup_vars["buy_now_price"].get())

            risk_per_share = buy_now - stop

            if risk_per_share <= 0:
                return

            shares = risk_dollar / risk_per_share
            total = shares * buy_now

            popup_vars["buy_now_shares"].set(round(shares, 2))
            popup_vars["buy_now_total"].set(round(total, 2))

        except Exception:
            return  # no silent logic corruption, just safe exit

    popup_vars["risk_dollar"].trace_add("write", popup_recalc)
    popup_vars["stop"].trace_add("write", popup_recalc)
    popup_vars["buy_now_price"].trace_add("write", popup_recalc)

    # ======================================================
    # NOTES TAB (FIXED ScrolledText)
    # ======================================================
    tk.Label(
        notes_tab,
        text="Trade Notes / Journal Notes",
        font=("Arial", 12, "bold"),
        bg="#f2f2f2"
    ).pack(anchor="w", padx=10, pady=(10,5))

    notes_text = scrolledtext.ScrolledText(notes_tab, wrap="word", font=("Courier", 10))
    notes_text.pack(fill="both", expand=True, padx=10, pady=10)
    notes_text.insert("1.0", row_data.get("trade_notes", ""))

    # ======================================================
    # ANALYSIS TAB
    # ======================================================
    analysis_text = scrolledtext.ScrolledText(analysis_tab, wrap="word", font=("Courier", 10))
    analysis_text.pack(fill="both", expand=True, padx=10, pady=10)
    analysis_text.insert("1.0", row_data.get("analysis_notes", ""))

    # ======================================================
    # MANAGEMENT TAB
    # ======================================================
    management_text = scrolledtext.ScrolledText(management_tab, wrap="word", font=("Courier", 10))
    management_text.pack(fill="both", expand=True, padx=10, pady=10)
    management_text.insert("1.0", row_data.get("management_notes", ""))

    # ======================================================
    # UPDATE FUNCTION
    # ======================================================
    def update_current_entry():

        try:
            updated_rows = []

            for row in journal_rows:

                if row.get("timestamp") == entry_timestamp:

                    updated_row = {}

                    for field in CSV_FIELDS:

                        if field == "timestamp":
                            updated_row[field] = entry_timestamp

                        elif field == "trade_notes":
                            updated_row[field] = notes_text.get("1.0", tk.END).strip()

                        elif field == "analysis_notes":
                            updated_row[field] = analysis_text.get("1.0", tk.END).strip()

                        elif field == "management_notes":
                            updated_row[field] = management_text.get("1.0", tk.END).strip()

                        elif field in popup_vars:
                            updated_row[field] = popup_vars[field].get()

                        else:
                            updated_row[field] = ""

                    updated_rows.append(updated_row)

                else:
                    updated_rows.append(row)

            with open(JOURNAL_FILE, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
                writer.writeheader()
                writer.writerows(updated_rows)

            if load_journal:
                load_journal()

            messagebox.showinfo("Updated", "Entry successfully updated.")
            popup.destroy()

        except Exception as e:
            messagebox.showerror("Update Error", str(e))

    # ======================================================
    # DELETE ENTRY
    # ======================================================
    def delete_current_entry():

        if delete_journal_entry:
            deleted = delete_journal_entry(entry_timestamp)

            if deleted:
                messagebox.showinfo("Deleted", "Journal entry deleted successfully.")
                popup.destroy()

    # ======================================================
    # BUTTON BAR
    # ======================================================
    bottom_frame = tk.Frame(popup, bg="#f2f2f2")
    bottom_frame.pack(fill="x", pady=5)

    tk.Button(bottom_frame, text="UPDATE CURRENT ENTRY",
              command=update_current_entry).pack(side="left", padx=10)

    tk.Button(bottom_frame, text="DELETE ENTRY",
              command=delete_current_entry).pack(side="left", padx=10)

    tk.Button(bottom_frame, text="CLOSE",
              command=popup.destroy).pack(side="right", padx=10)


# ==========================================================
# BIND (SAFE VERSION - MUST BE IN journal.py SCOPE)
# ==========================================================
# tree.bind("<Double-1>", lambda e: open_entry_editor(e, tree=tree, root=root, journal_rows=journal_rows, CSV_FIELDS=CSV_FIELDS, JOURNAL_FILE=JOURNAL_FILE, load_journal=load_journal, delete_journal_entry=delete_journal_entry, generate_signal_template=generate_signal_template))
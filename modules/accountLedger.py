import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import csv
import os
import uuid

from datetime import datetime

LEDGER_FILE = "account_ledger.csv"

LEDGER_FIELDS = [
    "id",
    "timestamp",
    "investor",
    "entry_class",
    "transaction_type",
    "debit",
    "credit",
    "gain_loss",
    "distribution",
    "equity_after",
    "ownership_pct",
    "notes"
]

# ==========================================================
# ACCOUNT JOURNAL
# ==========================================================        
ledger_rows = []

# ==========================================================
# SAFE FLOAT
# ==========================================================
def safe_float(value):
    try:
        if value is None or value == "":
            return 0.0
        return float(value)
    except:
        return 0.0
        
def map_entry_class(ui_type):
    mapping = {
        "Deposit": "capital_in",
        "Withdrawal": "capital_out",
        "Transfer": "capital_out",
        "Adjustment": "trade_pnl",
        "P&L": "trade_pnl"
    }
    return mapping.get(ui_type, ui_type) 

# ==========================================================
# EQUITY CHAIN
# ==========================================================
def rebuild_equity_chain():

    global ledger_rows

    running_equity = 0.0

    for row in ledger_rows:

        entry_class = str(
            row.get("entry_class", "")
        ).strip()

        debit = safe_float(row.get("debit", 0))
        credit = safe_float(row.get("credit", 0))
        gain_loss = safe_float(row.get("gain_loss", 0))
        distribution = safe_float(row.get("distribution", 0))

        if entry_class == "capital_in":

            running_equity += credit

        elif entry_class == "capital_out":

            running_equity -= debit

        elif entry_class == "trade_pnl":

            running_equity += gain_loss

        elif entry_class == "distribution":

            running_equity -= distribution

        row["equity_after"] = round(
            running_equity,
            2
        )
        
# ==========================================================
# CALCULATE LEDGER BALANCE
# ==========================================================
def calculate_ledger_balance():

    global ledger_rows

    if not ledger_rows:
        return 0.0

    rebuild_equity_chain()

    return round(
        safe_float(
            ledger_rows[-1].get(
                "equity_after",
                0
            )
        ),
        2
    )
    
# ==========================================================
# INVESTOR SNAPSHOT ENGINE
# ==========================================================
def calculate_investor_equity():

    global ledger_rows

    rebuild_equity_chain()

    total_equity = calculate_ledger_balance()

    investor_data = {}

    for row in ledger_rows:

        investor = str(
            row.get("investor", "")
        ).strip()

        if not investor:
            continue

        if investor.upper() == "FUND":
            continue

        if investor not in investor_data:

            investor_data[investor] = {
                "contributions": 0.0,
                "withdrawals": 0.0,
                "distributions": 0.0
            }

        entry_class = row.get(
            "entry_class",
            ""
        )

        debit = safe_float(
            row.get("debit", 0)
        )

        credit = safe_float(
            row.get("credit", 0)
        )

        distribution = safe_float(
            row.get("distribution", 0)
        )

        if entry_class == "capital_in":

            investor_data[investor][
                "contributions"
            ] += credit

        elif entry_class == "capital_out":

            investor_data[investor][
                "withdrawals"
            ] += debit

        elif entry_class == "distribution":

            investor_data[investor][
                "distributions"
            ] += distribution

    total_net_capital = 0.0

    for investor in investor_data:

        net_capital = (
            investor_data[investor]["contributions"]
            - investor_data[investor]["withdrawals"]
            - investor_data[investor]["distributions"]
        )

        investor_data[investor][
            "net_capital"
        ] = net_capital

        total_net_capital += net_capital

    if total_net_capital <= 0:

        for investor in investor_data:

            investor_data[investor].update({
                "ownership_pct": 0.0,
                "net_equity": 0.0,
                "gains_losses": 0.0
            })

        return investor_data, total_equity

    for investor in investor_data:

        ownership_pct = (
            investor_data[investor][
                "net_capital"
            ]
            /
            total_net_capital
        ) * 100

        net_equity = (
            total_equity
            *
            ownership_pct
            / 100
        )

        gains_losses = (
            net_equity
            -
            investor_data[investor][
                "net_capital"
            ]
        )

        investor_data[investor].update({

            "ownership_pct":
                round(
                    ownership_pct,
                    2
                ),

            "net_equity":
                round(
                    net_equity,
                    2
                ),

            "gains_losses":
                round(
                    gains_losses,
                    2
                )
        })

    return (
        investor_data,
        round(total_equity, 2)
    )
    
# ==========================================================
# BUILD INVESTOR SNAPSHOT
# ==========================================================
def build_investor_snapshot():

    investor_data, total_equity = calculate_investor_equity()

    snapshot = []

    for investor, data in investor_data.items():

        # FUND is ignored ONLY here
        if investor.upper() == "FUND":
            continue

        snapshot.append({
            "investor": investor,
            "contributions": data["contributions"],
            "withdrawals": data["withdrawals"],
            "gains_losses": data["gains_losses"],
            "distributions": data["distributions"],
            "net": data["net_equity"],
            "ownership_pct": data["ownership_pct"]
        })

    snapshot.sort(key=lambda x: x["net"], reverse=True)

    return snapshot
# ==========================================================
# LOAD LEDGER
# ==========================================================
def load_ledger():

    global ledger_rows

    ledger_rows.clear()

    if not os.path.isfile(
        LEDGER_FILE
    ):
        return

    with open(
        LEDGER_FILE,
        newline="",
        encoding="utf-8"
    ) as f:

        reader = csv.DictReader(f)

        for row in reader:

            ledger_rows.append(row)

    rebuild_equity_chain()
    
# ==========================================================
# DELETE LEDGER
# ==========================================================
def delete_ledger_entry(entry_id):

    global ledger_rows

    confirm = messagebox.askyesno(
        "Delete Entry",
        "Delete this ledger entry?"
    )

    if not confirm:
        return

    ledger_rows = [

        row

        for row in ledger_rows

        if row.get("id") != entry_id
    ]

    rebuild_equity_chain()

    with open(
        LEDGER_FILE,
        "w",
        newline="",
        encoding="utf-8"
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=LEDGER_FIELDS
        )

        writer.writeheader()

        for row in ledger_rows:

            writer.writerow({
                k: row.get(k, "")
                for k in LEDGER_FIELDS
            })

    load_ledger()
    
# ==========================================================
# UPDATE LEDGER
# ==========================================================
def update_ledger_entry(updated_row):

    global ledger_rows

    for i, row in enumerate(
        ledger_rows
    ):

        if row.get("id") == updated_row.get("id"):

            updated_row[
                "entry_class"
            ] = map_entry_class(
                updated_row[
                    "transaction_type"
                ]
            )

            ledger_rows[i] = updated_row

            break

    rebuild_equity_chain()

    with open(
        LEDGER_FILE,
        "w",
        newline="",
        encoding="utf-8"
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=LEDGER_FIELDS
        )

        writer.writeheader()

        for row in ledger_rows:

            writer.writerow({
                k: row.get(k, "")
                for k in LEDGER_FIELDS
            })

    load_ledger()
    
# ==========================================================
# SAVE LEDGER ENTRY
# ==========================================================
def save_ledger_entry(
    investor,
    entry_class,
    transaction_type,
    debit,
    credit,
    gain_loss,
    distribution,
    notes
):

    global ledger_rows

    row = {

        "id":
            str(uuid.uuid4())[:8],

        "timestamp":
            datetime.now().isoformat(),

        "investor":
            investor,

        "entry_class":
            entry_class,

        "transaction_type":
            transaction_type,

        "debit":
            round(
                safe_float(debit),
                2
            ),

        "credit":
            round(
                safe_float(credit),
                2
            ),

        "gain_loss":
            round(
                safe_float(gain_loss),
                2
            ),

        "distribution":
            round(
                safe_float(distribution),
                2
            ),

        "equity_after":
            0.0,

        "ownership_pct":
            0.0,

        "notes":
            notes
    }

    ledger_rows.append(row)

    rebuild_equity_chain()

    with open(
        LEDGER_FILE,
        "w",
        newline="",
        encoding="utf-8"
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=LEDGER_FIELDS
        )

        writer.writeheader()

        for r in ledger_rows:

            writer.writerow({
                k: r.get(k, "")
                for k in LEDGER_FIELDS
            })

    load_ledger()
    
# ==========================================================
# LEDGER POPUP WINDOW
# ==========================================================

def show_account_ledger_popup(root):

    load_ledger()

    popup = tk.Toplevel(root)

    popup.title("Account Ledger System")

    popup.geometry("1600x850")

    popup.configure(bg="#f2f2f2")

    # =====================================================
    # VARIABLES
    # =====================================================

    investor_var = tk.StringVar()
    type_var = tk.StringVar(value="Deposit")

    debit_var = tk.DoubleVar(value=0.0)
    credit_var = tk.DoubleVar(value=0.0)

    notes_var = tk.StringVar()

    filter_var = tk.StringVar()
    filter_type_var = tk.StringVar(value="investor")
    
    gain_loss_var = tk.DoubleVar(value=0.0)
    distribution_var = tk.DoubleVar(value=0.0)
    
    selected_entry_id = {"value": None}    
    
    # =====================================================
    # TOP INPUT FRAME
    # =====================================================

    top = tk.Frame(popup, bg="#f2f2f2")

    top.pack(fill="x", pady=10)

    tk.Label(
        top,
        text="Investor",
        font=("Arial", 10, "bold"),
        bg="#f2f2f2"
    ).grid(row=0, column=0, padx=5)

    tk.Entry(
        top,
        textvariable=investor_var,
        width=20
    ).grid(row=1, column=0, padx=5)

    tk.Label(
        top,
        text="Transaction Type",
        font=("Arial", 10, "bold"),
        bg="#f2f2f2"
    ).grid(row=0, column=1)

    ttk.Combobox(
        top,
        textvariable=type_var,
        values=[
            "Deposit",
            "Withdrawal",
            "Transfer",
            "Adjustment"
        ],
        state="readonly",
        width=18
    ).grid(row=1, column=1)

    tk.Label(
        top,
        text="Debit",
        font=("Arial", 10, "bold"),
        bg="#f2f2f2"
    ).grid(row=0, column=2)

    tk.Entry(
        top,
        textvariable=debit_var,
        width=12
    ).grid(row=1, column=2)

    tk.Label(
        top,
        text="Credit",
        font=("Arial", 10, "bold"),
        bg="#f2f2f2"
    ).grid(row=0, column=3)

    tk.Entry(
        top,
        textvariable=credit_var,
        width=12
    ).grid(row=1, column=3)

    tk.Label(
        top,
        text="Gain / Loss",
        font=("Arial", 10, "bold"),
        bg="#f2f2f2"
    ).grid(row=0, column=4)

    tk.Entry(
        top,
        textvariable=gain_loss_var,
        width=12
    ).grid(row=1, column=4)

    tk.Label(
        top,
        text="Distribution",
        font=("Arial", 10, "bold"),
        bg="#f2f2f2"
    ).grid(row=0, column=5)

    tk.Entry(
        top,
        textvariable=distribution_var,
        width=12
    ).grid(row=1, column=5)

    tk.Label(
        top,
        text="Notes",
        font=("Arial", 10, "bold"),
        bg="#f2f2f2"
    ).grid(row=0, column=6)

    tk.Entry(
        top,
        textvariable=notes_var,
        width=45
    ).grid(row=1, column=6, padx=5)

    # =====================================================
    # SNAPSHOT PANEL
    # =====================================================

    snapshot_frame = tk.LabelFrame(
        popup,
        text="Investor Snapshot",
        font=("Arial", 10, "bold"),
        bg="#f2f2f2"
    )

    snapshot_frame.pack(
        fill="x",
        padx=10,
        pady=5
    )

    snapshot_listbox = tk.Listbox(
        snapshot_frame,
        height=8,
        font=("Courier", 10)
    )

    snapshot_listbox.pack(
        fill="x",
        padx=5,
        pady=5
    )

    filter_frame = tk.Frame(
        popup,
        bg="#f2f2f2"
    )
    
    # =====================================================
    # TREEVIEW
    # =====================================================

    tree_frame = tk.Frame(popup)

    tree_frame.pack(
        fill="both",
        expand=True,
        padx=10,
        pady=10
    )

    vsb = tk.Scrollbar(tree_frame, orient="vertical")

    ledger_tree = ttk.Treeview(
        tree_frame,
        columns=LEDGER_FIELDS,
        show="headings",
        yscrollcommand=vsb.set
    )

    vsb.config(command=ledger_tree.yview)

    vsb.pack(side="right", fill="y")

    ledger_tree.pack(
        side="left",
        fill="both",
        expand=True
    )

    for col in LEDGER_FIELDS:

        ledger_tree.heading(col, text=col)

        ledger_tree.column(
            col,
            width=140,
            anchor="center"
        )

    # =====================================================
    # INVESTOR FILTER
    # =====================================================        
    def filter_by_investor(investor_name):
        ledger_tree.delete(*ledger_tree.get_children())

        for row in ledger_rows:
            if row.get("investor", "") == investor_name:
                values = [row.get(field, "") for field in LEDGER_FIELDS]

                ledger_tree.insert("", "end", values=values)    
            
    # =====================================================
    # REFRESH
    # =====================================================

    def refresh_ledger():

        # -----------------------------
        # FORCE DATA SYNC FIRST
        # -----------------------------
        load_ledger()

        ledger_tree.delete(*ledger_tree.get_children())

        search = filter_var.get().lower()
        ftype = filter_type_var.get()

        for row in ledger_rows:

            compare = str(row.get(ftype, "")).lower()

            if search in compare:

                values = []

                for field in LEDGER_FIELDS:

                    if field == "ownership_pct" and row.get("investor", "").upper() == "FUND":
                        values.append(0)
                    else:
                        values.append(row.get(field, ""))

                ledger_tree.insert("", "end", values=values)

        # -----------------------------
        # SNAPSHOT (ALWAYS FRESH DATA)
        # -----------------------------
        snapshot_listbox.delete(0, tk.END)

        total_balance = calculate_ledger_balance()

        snapshot_listbox.insert(
            tk.END,
            f"TOTAL ACCOUNT VALUE: ${total_balance:,.2f}"
        )

        snapshot = build_investor_snapshot()

        for item in snapshot:
            line = (
                f"{item['investor']} | "
                f"Net: ${item['net']:,.2f} | "
                f"Ownership: {item['ownership_pct']}%"
            )

            snapshot_listbox.insert(tk.END, line)

    # =====================================================
    # INVESTOR SELECTOR
    # =====================================================


    def on_snapshot_select(event):
        selection = snapshot_listbox.curselection()
        if not selection:
            return

        value = snapshot_listbox.get(selection[0])

        # ignore total row
        if "TOTAL ACCOUNT VALUE" in value:
            return

        # ✅ extract investor name BEFORE " | "
        investor_name = value.split("|")[0].strip()

        filter_by_investor(investor_name)

    snapshot_listbox.bind("<<ListboxSelect>>", on_snapshot_select)

    # =====================================================
    # SAVE BUTTON
    # =====================================================
    def submit():
        try:
            investor = investor_var.get().strip()

            if not investor:
                messagebox.showerror("Error", "Investor required")
                return

            entry_class = map_entry_class(type_var.get())

            save_ledger_entry(
                investor=investor,
                entry_class=entry_class,
                transaction_type=type_var.get(),
                debit=safe_float(debit_var.get()),
                credit=safe_float(credit_var.get()),
                gain_loss=safe_float(gain_loss_var.get()),
                distribution=safe_float(distribution_var.get()),
                notes=notes_var.get()
            )

            # FORCE UI RESET (prevents "" issues)
            debit_var.set(0.0)
            credit_var.set(0.0)
            gain_loss_var.set(0.0)
            distribution_var.set(0.0)
            notes_var.set("")

            load_ledger()          # 🔥 FORCE reload FIRST
            refresh_ledger()       # THEN rebuild UI

        except Exception as e:
            messagebox.showerror("Submit Error", str(e))

    tk.Button(
        top,
        text="POST ENTRY",
        bg="#2e7d32",
        fg="white",
        font=("Arial", 10, "bold"),
        command=submit
    ).grid(row=1, column=7, padx=10)


    # =====================================================
    # CLEAR FILTERS BUTTON
    # =====================================================
    def clear_filters():
        filter_var.set("")
        filter_type_var.set("investor")  # optional reset (or keep last used)
        refresh_ledger()

    tk.Button(
        top,
        text="CLEAR FILTERS",
        bg="#616161",
        fg="white",
        font=("Arial", 10, "bold"),
        command=clear_filters
    ).grid(row=1, column=8, padx=10)
            
    # =====================================================
    # FILTERS
    # =====================================================


    filter_frame.pack(fill="x")

    ttk.Combobox(
        filter_frame,
        textvariable=filter_type_var,
        values=[
            "investor",
            "transaction_type",
            "timestamp"
        ],
        state="readonly",
        width=20
    ).pack(side="left", padx=5)

    tk.Entry(
        filter_frame,
        textvariable=filter_var,
        width=35
    ).pack(side="left", padx=5)

    filter_var.trace_add(
        "write",
        lambda *args: refresh_ledger()
    )

    filter_type_var.trace_add(
        "write",
        lambda *args: refresh_ledger()
    )

        
    load_ledger()
    refresh_ledger()    

    # =====================================================
    # LOAD + EDIT ENTRY POPUP
    # =====================================================

    def load_selected_entry(event):

        selected = ledger_tree.selection()

        if not selected:
            return

        item = selected[0]

        values = ledger_tree.item(item, "values")

        row_data = dict(zip(LEDGER_FIELDS, values))

        selected_entry_id["value"] = row_data["id"]

        # ================================================
        # EDIT POPUP
        # ================================================

        edit_popup = tk.Toplevel(popup)

        edit_popup.title("Edit Ledger Entry")

        edit_popup.geometry("700x300")

        edit_popup.configure(bg="#f2f2f2")

        # VARIABLES
        investor_edit = tk.StringVar(value=row_data["investor"])
        type_edit = tk.StringVar(value=row_data["transaction_type"])

        debit_edit = tk.DoubleVar(
            value=safe_float(row_data["debit"])
        )

        credit_edit = tk.DoubleVar(
            value=safe_float(row_data["credit"])
        )

        gain_loss_edit = tk.DoubleVar(
            value=safe_float(row_data["gain_loss"])
        )

        distribution_edit = tk.DoubleVar(
            value=safe_float(row_data["distribution"])
        )

        notes_edit = tk.StringVar(
            value=row_data["notes"]
        )

        # =================================================
        # FORM
        # =================================================

        form = tk.Frame(edit_popup, bg="#f2f2f2")

        form.pack(fill="both", expand=True, padx=10, pady=10)

        labels = [
            "Investor",
            "Type",
            "Debit",
            "Credit",
            "Gain/Loss",
            "Distribution",
            "Notes"
        ]

        for i, text in enumerate(labels):

            tk.Label(
                form,
                text=text,
                font=("Arial", 10, "bold"),
                bg="#f2f2f2"
            ).grid(row=0, column=i, padx=5, pady=5)

        tk.Entry(
            form,
            textvariable=investor_edit,
            width=15
        ).grid(row=1, column=0)

        ttk.Combobox(
            form,
            textvariable=type_edit,
            values=[
                "Deposit",
                "Withdrawal",
                "Transfer",
                "Adjustment"
            ],
            state="readonly",
            width=14
        ).grid(row=1, column=1)

        tk.Entry(
            form,
            textvariable=debit_edit,
            width=10
        ).grid(row=1, column=2)

        tk.Entry(
            form,
            textvariable=credit_edit,
            width=10
        ).grid(row=1, column=3)

        tk.Entry(
            form,
            textvariable=gain_loss_edit,
            width=10
        ).grid(row=1, column=4)

        tk.Entry(
            form,
            textvariable=distribution_edit,
            width=10
        ).grid(row=1, column=5)

        tk.Entry(
            form,
            textvariable=notes_edit,
            width=25
        ).grid(row=1, column=6)

        # =================================================
        # SAVE UPDATE
        # =================================================

        def save_edit():

            updated_row = {
                "id": row_data["id"],
                "timestamp": row_data["timestamp"],
                "investor": investor_edit.get(),
                "transaction_type": type_edit.get(),
                "debit": round(debit_edit.get(), 2),
                "credit": round(credit_edit.get(), 2),
                "gain_loss": round(gain_loss_edit.get(), 2),
                "distribution": round(distribution_edit.get(), 2),
                "equity_after": row_data["equity_after"],
                "ownership_pct": row_data["ownership_pct"],
                "notes": notes_edit.get()
            }

            update_ledger_entry(updated_row)

            refresh_ledger()

            edit_popup.destroy()

            messagebox.showinfo(
                "Updated",
                "Ledger entry updated."
            )

        # =================================================
        # DELETE ENTRY
        # =================================================

        def delete_edit():

            delete_ledger_entry(row_data["id"])

            refresh_ledger()

            edit_popup.destroy()

        # BUTTONS

        button_frame = tk.Frame(
            edit_popup,
            bg="#f2f2f2"
        )

        button_frame.pack(pady=20)

        tk.Button(
            button_frame,
            text="SAVE CHANGES",
            bg="#2e7d32",
            fg="white",
            font=("Arial", 10, "bold"),
            command=save_edit
        ).pack(side="left", padx=10)

        tk.Button(
            button_frame,
            text="DELETE ENTRY",
            bg="#c62828",
            fg="white",
            font=("Arial", 10, "bold"),
            command=delete_edit
        ).pack(side="left", padx=10)
    
    # =================================================
    # BIND DOUBLE CLICK
    # =================================================

    ledger_tree.bind(
        "<Double-1>",
        load_selected_entry
    )
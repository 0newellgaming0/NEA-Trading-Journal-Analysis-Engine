"""
====================================================================
NEA28 SEC EDGAR FETCHER ENGINE
Module:
    secFetcher.py

Purpose
-------
SEC filing ingestion engine using edgartools.

Designed for:
- Institutional Accumulation Analysis
- Fundamental Scoring Engine
- Growth Asymmetry Detection
- SEC Filing Intelligence
- ML Feature Generation
- Financial Health Analysis

Source:
    https://github.com/dgunning/edgartools

Replaces:
    yfinance financial statement extraction

Stores:
    - Company metadata
    - SEC filing history
    - XBRL financial facts
    - Income statements
    - Balance sheets
    - Cash flow statements


Architecture:
    SEC EDGAR
          |
          v
    sec_edgar_fetcher.py
          |
          v
    FinancialRepository
          |
          v
    SQLite trading database


SQLite remains SOURCE OF TRUTH.
====================================================================
"""


import os
import json
import sqlite3
import threading

import pandas as pd
import tkinter as tk

from tkinter import ttk, scrolledtext

from datetime import datetime, timedelta


from edgar import (
    Company,
    set_identity
)


from modules.path_resolver import (
    get_watchlist_db_path,
    get_project_root,
    get_financials_root,
    get_sec_financials_root
)

from modules.stock_data_db.sec_financials_db.sec_repository import (
    SECFinancialRepository
)

from modules.secAnalysis import (
    SECAnalysisEngine
)


from modules.stock_data_db.init_db import (
    init_all
)


init_all()

# =========================================================
# PATH CONFIGURATION
# =========================================================

SEC_HISTORY_YEARS = 7

SEC_CUTOFF_DATE = (
    datetime.now() - timedelta(days=365 * SEC_HISTORY_YEARS)
).date()

WATCHLIST_DB = get_watchlist_db_path()


SEC_FINANCIALS_DIR = get_sec_financials_root()


PROJECT_ROOT = get_project_root()


SEC_CACHE_DIR = os.path.join(
    SEC_FINANCIALS_DIR,
    "SEC"
)


os.makedirs(
    SEC_CACHE_DIR,
    exist_ok=True
)

# =========================================================
# SEC IDENTITY
# =========================================================


def configure_sec_identity():

    try:

        set_identity(
            "Newell Trading Group research@example.com"
        )


        log(
            "SEC identity configured"
        )


        return True


    except Exception as e:

        log(
            f"SEC identity error: {e}"
        )

        return False
        
        
        
# =========================================================
# GLOBAL UI HOOKS
# =========================================================


dashboard = None

dashboard_log = None

# =========================================================
# LOGGING
# =========================================================


def log(msg):

    timestamp = datetime.now().strftime(
        "%H:%M:%S"
    )


    if dashboard_log is None:

        print(
            f"[{timestamp}] {msg}"
        )

        return



    def write():

        dashboard_log.configure(
            state="normal"
        )

        dashboard_log.insert(
            tk.END,
            f"[{timestamp}] {msg}\n"
        )


        dashboard_log.see(
            tk.END
        )


        dashboard_log.configure(
            state="disabled"
        )



    dashboard.after(
        0,
        write
    )

# =========================================================
# WATCHLIST SOURCE
# =========================================================


def load_tickers_from_watchlist():

    try:

        log(
            "Loading SEC ticker universe..."
        )


        if not os.path.exists(
            WATCHLIST_DB
        ):

            log(
                "Watchlist database missing"
            )

            return []



        conn = sqlite3.connect(
            WATCHLIST_DB
        )


        cur = conn.cursor()



        cur.execute(
            """
            SELECT ticker
            FROM watchlist
            """
        )


        rows = cur.fetchall()



        conn.close()



        tickers = sorted(
            {
                row[0]
                .strip()
                .upper()

                for row in rows
                if row[0]
            }
        )



        log(
            f"Loaded {len(tickers)} tickers"
        )


        return tickers



    except Exception as e:

        log(
            f"Watchlist error: {e}"
        )

        return []

# =========================================================
# SEC COMPANY LOADER
# =========================================================


def load_sec_company(ticker):

    try:

        ticker = ticker.upper().strip()


        log(
            f"SEC loading company: {ticker}"
        )


        company = Company(
            ticker
        )


        if company is None:

            log(
                f"SEC company not found: {ticker}"
            )

            return None



        log(
            f"SEC company loaded: {ticker}"
        )


        return company



    except Exception as e:

        log(
            f"SEC company load failed {ticker}: {e}"
        )

        return None

# =========================================================
# SEC DIRECTORY MANAGER
# =========================================================


def create_sec_company_directory(ticker):

    try:

        ticker = ticker.upper()


        base_dir = os.path.join(
            SEC_CACHE_DIR,
            ticker
        )


        os.makedirs(
            base_dir,
            exist_ok=True
        )


        return base_dir



    except Exception as e:

        log(
            f"SEC directory error {ticker}: {e}"
        )

        return None

# =========================================================
# COMPANY METADATA
# =========================================================


def save_company_metadata(
        ticker,
        company
):

    try:

        base_dir = create_sec_company_directory(
            ticker
        )


        metadata = {

            "source":
                "SEC_EDGAR",

            "ticker":
                ticker,

            "company_name":
                getattr(
                    company,
                    "name",
                    None
                ),

            "cik":
                getattr(
                    company,
                    "cik",
                    None
                ),

            "timestamp":
                datetime.now()
                .isoformat()

        }



        path = os.path.join(
            base_dir,
            "metadata.json"
        )


        with open(
            path,
            "w"
        ) as f:

            json.dump(
                metadata,
                f,
                indent=4,
                default=str
            )


        log(
            f"Metadata saved: {ticker}"
        )


        return metadata



    except Exception as e:

        log(
            f"Metadata error {ticker}: {e}"
        )

        return None

# =========================================================
# SEC FILING RETRIEVAL
# =========================================================

def fetch_sec_filings(ticker, company):
    try:
        log(f"Retrieving SEC filings {ticker}")

        filings = company.get_filings(
            form=["10-K", "10-Q", "8-K"]
        )

        if filings is None:
            log(f"No filings found {ticker}")
            return None

        records = []

        for filing in filings.head(40):
            records.append({
                "ticker": ticker.upper().strip(),
                "accession_number": getattr(filing, "accession_no", None),
                "form": getattr(filing, "form", None),
                "filing_date": getattr(filing, "filing_date", None),
                "report_date": getattr(filing, "report_date", None),
                "document": getattr(filing, "primary_document", None)
            })

        if not records:
            log(f"No filing records generated {ticker}")
            return None

        filings_df = pd.DataFrame(records)

        if "filing_date" in filings_df.columns:
            filings_df["filing_date"] = pd.to_datetime(
                filings_df["filing_date"],
                errors="coerce"
            ).dt.date

            filings_df = filings_df[
                filings_df["filing_date"] >= SEC_CUTOFF_DATE
            ]

        if filings_df.empty:
            log(f"No SEC filings within cutoff window {ticker}")
            return None

        base_dir = create_sec_company_directory(ticker)

        filings_df.to_csv(
            os.path.join(base_dir, "filings.csv"),
            index=False
        )

        repo = SECFinancialRepository()

        log(f"Writing SEC filings to database: {ticker}")

        repo.insert_filings(
            ticker,
            filings_df
        )

        count = repo.conn.execute(
            """
            SELECT COUNT(*)
            FROM sec_filings
            WHERE ticker=?
            """,
            (ticker.upper().strip(),)
        ).fetchone()[0]

        repo.close()

        log(
            f"SEC filings saved {ticker} "
            f"({count} total records)"
        )

        return filings_df

    except Exception as e:
        log(f"SEC filing retrieval failed {ticker}: {e}")
        return None
        
# =========================================================
# SEC FILING HISTORY
# =========================================================

def fetch_sec_financials(ticker):
    try:
        configure_sec_identity()

        log(f"[SEC_FETCHER] START {ticker}")

        company = load_sec_company(ticker)

        if company is None:
            return False

        save_company_metadata(
            ticker,
            company
        )

        repo = SECFinancialRepository()

        repo.delete_company_data(
            ticker
        )

        filings = fetch_sec_filings(
            ticker,
            company
        )

        facts_df = fetch_xbrl_facts(
            ticker,
            company
        )

        if facts_df is None or facts_df.empty:
            log(f"No XBRL facts {ticker}")
            return False

        income_df = extract_income_statement(
            ticker,
            facts_df
        )

        balance_df = extract_balance_sheet(
            ticker,
            facts_df
        )

        cashflow_df = extract_cashflow(
            ticker,
            facts_df
        )

        repo.insert_xbrl_facts(
            ticker,
            facts_df
        )

        if income_df is not None:
            repo.insert_statement(
                ticker,
                "income_statement",
                income_df
            )

        if balance_df is not None:
            repo.insert_statement(
                ticker,
                "balance_sheet",
                balance_df
            )

        if cashflow_df is not None:
            repo.insert_statement(
                ticker,
                "cashflow_statement",
                cashflow_df
            )

        log(
            f"[SEC_FETCHER] Stored financial statements: {ticker}"
        )

        repo.close()

        log(
            f"[SEC_FETCHER] Stored {len(facts_df)} XBRL facts"
        )

        analysis = SECAnalysisEngine()

        report = analysis.analyze_company(
            ticker
        )

        analysis.close()

        log(
            f"[SEC_FETCHER] COMPLETE {ticker}"
        )

        return True

    except Exception as e:
        log(
            f"SEC fetch failed {ticker}: {e}"
        )
        return False
        
# =========================================================
# FILTER FILINGS
# =========================================================


def filter_filings(
        filings_df,
        forms=None
):

    try:

        if filings_df is None:

            return None



        if forms is None:

            forms = [
                "10-K",
                "10-Q",
                "8-K"
            ]



        filtered = filings_df[
            filings_df["form"]
            .isin(forms)
        ].copy()



        return filtered



    except Exception as e:

        log(
            f"Filter filings error: {e}"
        )

        return None

# =========================================================
# LATEST FINANCIAL FILINGS
# =========================================================


def get_latest_financial_filings(
        ticker,
        company
):

    try:

        log(
            f"Searching latest filings {ticker}"
        )


        filings = company.get_filings(
            form=[
                "10-K",
                "10-Q"
            ]
        )


        if filings is None:

            return None



        latest = filings.head(
            10
        )



        return latest



    except Exception as e:

        log(
            f"Latest filings error {ticker}: {e}"
        )

        return None

# =========================================================
# XBRL FACT EXTRACTION
# =========================================================


def fetch_xbrl_facts(
        ticker,
        company
):

    try:

        log(
            f"Extracting XBRL facts {ticker}"
        )


        facts = company.get_facts()



        if facts is None:

            log(
                "No XBRL facts found"
            )

            return None



        df = facts.to_dataframe()



        if df.empty:

            return None



        df.columns = [
            str(c)
            .strip()
            .lower()
            .replace(
                " ",
                "_"
            )

            for c in df.columns
        ]



        rename_map = {

            "val": "value",
            "fy": "fiscal_year",
            "fp": "fiscal_period",
            "filed": "filing_date",
            "end": "period_end",
            "start": "period_start"

        }



        df = df.rename(
            columns=rename_map
        )



        df = filter_sec_history(
            df
        )



        if df.empty:

            log(
                f"No XBRL facts within 3 years {ticker}"
            )

            return None



        base_dir = create_sec_company_directory(
            ticker
        )



        df.to_csv(
            os.path.join(
                base_dir,
                "facts.csv"
            ),
            index=False
        )



        log(
            f"XBRL facts saved {ticker}"
        )


        return df



    except Exception as e:

        log(
            f"XBRL extraction failed {ticker}: {e}"
        )

        return None

# =========================================================
# SEC DATA NORMALIZATION
# =========================================================


def normalize_sec_dataframe(df):

    try:

        if df is None:

            return None



        df = df.copy()



        df.columns = [

            str(c)
            .strip()
            .lower()
            .replace(
                " ",
                "_"
            )

            for c in df.columns

        ]



        return df



    except Exception as e:

        log(
            f"SEC normalization failed: {e}"
        )

        return df

# =========================================================
# SEC THREE YEAR HISTORY FILTER
# =========================================================


def filter_sec_history(df):

    try:

        if df is None or df.empty:

            return df


        df = df.copy()


        if "filing_date" in df.columns:

            df["filing_date"] = pd.to_datetime(
                df["filing_date"],
                errors="coerce"
            )


            df = df[
                df["filing_date"] >= pd.Timestamp(
                    SEC_CUTOFF_DATE
                )
            ]


        elif "period_end" in df.columns:

            df["period_end"] = pd.to_datetime(
                df["period_end"],
                errors="coerce"
            )


            df = df[
                df["period_end"] >= pd.Timestamp(
                    SEC_CUTOFF_DATE
                )
            ]


        return df


    except Exception as e:

        log(
            f"SEC history filter failed: {e}"
        )

        return df
        
# =========================================================
# SEC INCOME STATEMENT EXTRACTION
# =========================================================


def extract_income_statement(
        ticker,
        facts_df
):

    try:

        log(
            f"Extracting income statement: {ticker}"
        )


        df = facts_df.copy()



        if df.empty:

            return None



        income_keywords = [

            "Revenue",
            "SalesRevenue",
            "Revenues",

            "GrossProfit",

            "OperatingIncomeLoss",

            "NetIncomeLoss",

            "EarningsPerShare"

        ]



        mask = df["concept"].astype(str).apply(

            lambda x:

            any(

                key.lower()
                in x.lower()

                for key in income_keywords

            )

        )



        income_df = df[mask].copy()



        income_df = normalize_sec_dataframe(
            income_df
        )


        income_df = filter_sec_history(
            income_df
        )


        if income_df.empty:

            log(
                f"No income statement history within 3 years {ticker}"
            )

            return None



        base_dir = create_sec_company_directory(
            ticker
        )


        income_df.to_csv(

            os.path.join(
                base_dir,
                "income_statement.csv"
            ),

            index=False

        )


        log(
            f"Income statement extracted: {ticker}"
        )


        return income_df



    except Exception as e:

        log(
            f"Income extraction failed {ticker}: {e}"
        )

        return None

# =========================================================
# SEC BALANCE SHEET EXTRACTION
# =========================================================


def extract_balance_sheet(
        ticker,
        facts_df
):

    try:

        log(
            f"Extracting balance sheet: {ticker}"
        )


        if facts_df is None or facts_df.empty:

            return None



        df = facts_df.copy()



        balance_keywords = [

            "Assets",

            "Liabilities",

            "StockholdersEquity",

            "CashAndCashEquivalents",

            "Debt",

            "Inventory",

            "AccountsReceivable"

        ]



        mask = df["concept"].astype(str).apply(

            lambda x:

            any(

                key.lower()
                in x.lower()

                for key in balance_keywords

            )

        )



        balance_df = df[mask].copy()



        balance_df = normalize_sec_dataframe(
            balance_df
        )


        balance_df = filter_sec_history(
            balance_df
        )



        if balance_df.empty:

            log(
                f"No balance sheet history within SEC window {ticker}"
            )

            return None



        base_dir = create_sec_company_directory(
            ticker
        )


        balance_df.to_csv(

            os.path.join(
                base_dir,
                "balance_sheet.csv"
            ),

            index=False

        )


        log(
            f"Balance sheet extracted: {ticker}"
        )


        return balance_df



    except Exception as e:

        log(
            f"Balance extraction failed {ticker}: {e}"
        )

        return None

# =========================================================
# SEC CASH FLOW EXTRACTION
# =========================================================


def extract_cashflow(
        ticker,
        facts_df
):

    try:

        log(
            f"Extracting cash flow: {ticker}"
        )


        if facts_df is None or facts_df.empty:

            return None



        df = facts_df.copy()



        cash_keywords = [

            "CashFlow",

            "NetCashProvided",

            "OperatingActivities",

            "InvestingActivities",

            "FinancingActivities",

            "Depreciation"

        ]



        mask = df["concept"].astype(str).apply(

            lambda x:

            any(

                key.lower()
                in x.lower()

                for key in cash_keywords

            )

        )



        cash_df = df[mask].copy()



        cash_df = normalize_sec_dataframe(
            cash_df
        )


        cash_df = filter_sec_history(
            cash_df
        )



        if cash_df.empty:

            log(
                f"No cashflow history within SEC window {ticker}"
            )

            return None



        base_dir = create_sec_company_directory(
            ticker
        )


        cash_df.to_csv(

            os.path.join(
                base_dir,
                "cashflow.csv"
            ),

            index=False

        )


        log(
            f"Cash flow extracted: {ticker}"
        )


        return cash_df



    except Exception as e:

        log(
            f"Cashflow extraction failed {ticker}: {e}"
        )

        return None

# =========================================================
# DATABASE STORAGE
# =========================================================


def save_sec_statement(
        ticker,
        statement_name,
        df
):

    try:

        if df is None or df.empty:

            log(
                f"Skipped empty SEC statement {statement_name}"
            )

            return False



        repo = SECFinancialRepository()



        # Remove records older than rolling SEC window

        if hasattr(
            repo,
            "cleanup_old_records"
        ):

            repo.cleanup_old_records(
                ticker,
                SEC_CUTOFF_DATE
            )


        repo.insert_statement(
            ticker,
            statement_name,
            df
        )



        log(
            f"SEC SQLite saved: {ticker} {statement_name}"
        )



        repo.close()



        return True



    except Exception as e:

        log(
            f"SEC repository error {ticker}: {e}"
        )

        return False

def save_xbrl_facts(
        ticker,
        df
):
    try:
        if df is None or df.empty:
            log(
                f"Skipped empty XBRL facts {ticker}"
            )
            return False

        repo = SECFinancialRepository()

        if hasattr(
            repo,
            "cleanup_old_records"
        ):
            repo.cleanup_old_records(
                ticker,
                SEC_CUTOFF_DATE
            )

        repo.insert_xbrl_facts(
            ticker,
            df
        )

        log(
            f"SEC SQLite saved XBRL facts: {ticker} ({len(df)} records)"
        )

        repo.close()

        return True

    except Exception as e:
        log(
            f"XBRL repository error {ticker}: {e}"
        )
        return False
        
# =========================================================
# FULL SEC UPDATE ENGINE
# =========================================================


def run_sec_update_all():

    try:

        log(
            "Starting SEC universe update"
        )


        tickers = load_tickers_from_watchlist()



        total = len(tickers)



        for i, ticker in enumerate(
            tickers,
            1
        ):

            log(
                f"Processing {ticker} {i}/{total}"
            )


            fetch_sec_financials(
                ticker
            )



        log(
            "SEC universe update complete"
        )



    except Exception as e:

        log(
            f"SEC batch error: {e}"
        )

# =========================================================
# SINGLE SEC UPDATE
# =========================================================


def run_sec_update_single(
        ticker
):

    try:

        log(
            f"SEC single update: {ticker}"
        )


        success = fetch_sec_financials(
            ticker
        )


        if success:

            log(
                f"SEC completed successfully: {ticker}"
            )

        else:

            log(
                f"SEC update failed: {ticker}"
            )


    except Exception as e:

        log(
            f"Single SEC error {ticker}: {e}"
        )

# =========================================================
# SEC UPDATE PREVIEW
# =========================================================


def build_sec_tab(parent):

    frame = parent

    try:

        tickers = load_tickers_from_watchlist()

        if not tickers:
            log("No tickers found in watchlist")
            return


        tk.Label(
            frame,
            text=f"{len(tickers)} tickers ready",
            font=("Arial", 12, "bold")
        ).pack(pady=10)


        box = tk.Listbox(frame)

        for ticker in tickers:
            box.insert(tk.END, ticker)

        box.pack(
            fill=tk.BOTH,
            expand=True
        )


        def start_all():

            threading.Thread(
                target=run_sec_update_all,
                daemon=True
            ).start()


        def start_single():

            selected = box.curselection()

            if not selected:
                log("No ticker selected")
                return

            ticker = box.get(selected[0])

            threading.Thread(
                target=run_sec_update_single,
                args=(ticker,),
                daemon=True
            ).start()


        buttons = tk.Frame(frame)
        buttons.pack()


        tk.Button(
            buttons,
            text="ALL SEC UPDATE",
            command=start_all
        ).pack(side=tk.LEFT)


        tk.Button(
            buttons,
            text="SELECT",
            command=start_single
        ).pack(side=tk.LEFT)

    except Exception as e:
        log(f"SEC preview error: {e}")

# =========================================================
# SEC DASHBOARD UI
# =========================================================


def main():

    global dashboard
    global dashboard_log



    dashboard = tk.Tk()



    dashboard.title(

        "NEA28 SEC EDGAR Financial Downloader"

    )



    dashboard.geometry(

        "950x700"

    )



    ttk.Label(

        dashboard,

        text="SEC EDGAR Financial Downloader",

        font=(

            "Arial",

            18

        )

    ).pack(

        pady=10

    )



    ttk.Button(

        dashboard,

        text="Update SEC Data",

        command=run_sec_update

    ).pack(

        pady=5

    )



    dashboard_log = scrolledtext.ScrolledText(

        dashboard,

        height=30

    )


    dashboard_log.pack(

        fill=tk.BOTH,

        expand=True

    )



    dashboard.mainloop()

# =========================================================
# ENTRY POINT
# =========================================================


if __name__ == "__main__":


    main()    
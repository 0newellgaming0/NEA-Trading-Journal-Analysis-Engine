"""
====================================================================
NEA28 SEC FINANCIAL REPOSITORY

Module:
    sec_repository.py

Database:
    secFinancials.db
    secAnalysis.db

Purpose
-------
SQLite repository layer for SEC EDGAR financial intelligence.

SQLite is the source of truth.

Author:
    Newell Trading Group
====================================================================
"""

import sqlite3
import json
import logging
from datetime import datetime

import pandas as pd

from modules.path_resolver import (
    get_sec_financial_db_path,
    get_sec_analysis_db_path
)

SEC_DB_PATH = get_sec_financial_db_path()
SEC_ANALYSIS_DB_PATH = get_sec_analysis_db_path()

logger = logging.getLogger("SECRepository")


# ============================================================
# COMMON HELPERS
# ============================================================

def utc_now():
    return datetime.utcnow().isoformat()


def normalize_columns(df):
    df = df.copy()
    df.columns = [
        str(c).strip().lower().replace(" ", "_")
        for c in df.columns
    ]
    return df


def sqlite_value(value):
    if pd.isna(value):
        return None
    if isinstance(value, pd.Timestamp):
        return value.strftime("%Y-%m-%d")
    if isinstance(value, datetime):
        return value.isoformat()
    return value


# ============================================================
# SEC FINANCIAL REPOSITORY
# ============================================================

class SECFinancialRepository:

    """
    Database access layer for secFinancials.db.

    No analysis.
    No scoring.
    No classification.

    Only persistence and retrieval.
    """

    def __init__(self):
        self.conn = sqlite3.connect(SEC_DB_PATH)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        self.initialize()


    def initialize(self):
        self.cursor.execute("""
            SELECT name
            FROM sqlite_master
            WHERE type='table'
            AND name='sec_company'
        """)

        result = self.cursor.fetchone()

        if result is None:
            raise RuntimeError(
                "SEC database schema missing. Run init_sec_db() first."
            )

        logger.info(
            "SEC financial database schema validated"
        )


    # ========================================================
    # DELETE COMPANY DATA
    # ========================================================

    def delete_company_data(self, ticker):

        ticker = ticker.upper().strip()

        for table in [
            "sec_filings",
            "sec_facts",
            "sec_statements",
            "sec_ingestion_log",
            "sec_company"        
        ]:
            self.cursor.execute(
                f"DELETE FROM {table} WHERE ticker=?",
                (ticker,)
            )

        self.conn.commit()

        logger.info(
            "Deleted existing SEC data: %s",
            ticker
        )


    def delete_xbrl_facts(self, ticker):

        self.cursor.execute(
            """
            DELETE FROM sec_facts
            WHERE ticker=?
            """,
            (ticker.upper(),)
        )

        self.conn.commit()


        logger.info(
            "Deleted XBRL facts: %s",
            ticker
        )


    def delete_statements(self, ticker):

        self.cursor.execute(
            """
            DELETE FROM sec_statements
            WHERE ticker=?
            """,
            (ticker.upper(),)
        )

        self.conn.commit()

        logger.info(
            "Deleted financial statements: %s",
            ticker
        )


    # ========================================================
    # COMPANY
    # ========================================================

    def insert_company(self, ticker, company):

        self.cursor.execute(
            """
            INSERT OR REPLACE INTO sec_company
            (
                ticker,
                cik,
                company_name,
                sic,
                exchange,
                industry,
                created_at
            )
            VALUES (?,?,?,?,?,?,?)
            """,
            (
                ticker.upper(),
                str(getattr(company, "cik", "")),
                getattr(company, "name", ""),
                getattr(company, "sic", ""),
                getattr(company, "exchange", ""),
                getattr(company, "industry", ""),
                utc_now()
            )
        )

        self.conn.commit()


    # ========================================================
    # FILINGS
    # ========================================================

    def insert_filings(self, ticker, filings_df):

        if filings_df is None or filings_df.empty:
            return

        filings_df = normalize_columns(filings_df)

        for _, row in filings_df.iterrows():

            self.cursor.execute(
                """
                INSERT OR IGNORE INTO sec_filings
                (
                    ticker,
                    accession_number,
                    form,
                    filing_date,
                    report_date,
                    filing_url,
                    document,
                    created_at
                )
                VALUES (?,?,?,?,?,?,?,?)
                """,
                (
                    ticker.upper(),
                    row.get("accession_number"),
                    row.get("form"),
                    row.get("filing_date"),
                    row.get("report_date"),
                    row.get("filing_url"),
                    row.get("document"),
                    utc_now()
                )
            )

        self.conn.commit()


    # ========================================================
    # XBRL FACTS
    # ========================================================

    def insert_xbrl_facts(self, ticker, facts_df):

        if facts_df is None or facts_df.empty:
            return False

        facts_df = normalize_columns(facts_df)

        for _, row in facts_df.iterrows():

            self.cursor.execute(
                """
                INSERT OR IGNORE INTO sec_facts
                (
                    ticker,
                    concept,
                    label,
                    value,
                    numeric_value,
                    unit,
                    period_type,
                    period_start,
                    period_end,
                    fiscal_year,
                    fiscal_period,
                    filing_date,
                    form,
                    accession_number,
                    created_at
                )
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    ticker.upper(),
                    sqlite_value(row.get("concept")),
                    sqlite_value(row.get("label")),
                    sqlite_value(row.get("value")),
                    sqlite_value(row.get("numeric_value")),
                    sqlite_value(row.get("unit")),
                    sqlite_value(row.get("period_type")),
                    sqlite_value(row.get("period_start")),
                    sqlite_value(row.get("period_end")),
                    sqlite_value(row.get("fiscal_year")),
                    sqlite_value(row.get("fiscal_period")),
                    sqlite_value(row.get("filing_date")),
                    sqlite_value(row.get("form")),
                    sqlite_value(row.get("accession_number")),
                    utc_now()
                )
            )

        self.conn.commit()

        return True
        
    # ========================================================
    # STATEMENTS
    # ========================================================

    def insert_statement(self, ticker, statement_type, df):

        if df is None or df.empty:
            return False

        df = normalize_columns(df)

        data_json = json.dumps(
            df.astype(str).to_dict(
                orient="records"
            ),
            default=str
        )

        self.cursor.execute(
            """
            DELETE FROM sec_statements
            WHERE ticker=?
            AND statement_type=?
            """,
            (
                ticker.upper(),
                statement_type
            )
        )

        self.cursor.execute(
            """
            INSERT INTO sec_statements
            (
                ticker,
                statement_type,
                fiscal_period,
                fiscal_year,
                period_end,
                data_json,
                created_at
            )
            VALUES (?,?,?,?,?,?,?)
            """,
            (
                ticker.upper(),
                statement_type,
                "LATEST",
                "",
                None,
                data_json,
                utc_now()
            )
        )

        self.conn.commit()

        return True


    # ========================================================
    # RETRIEVAL
    # ========================================================

    def get_company(self, ticker):

        return pd.read_sql_query(
            """
            SELECT *
            FROM sec_company
            WHERE ticker=?
            """,
            self.conn,
            params=(ticker.upper(),)
        )


    def get_filings(self, ticker):

        return pd.read_sql_query(
            """
            SELECT *
            FROM sec_filings
            WHERE ticker=?
            ORDER BY filing_date DESC
            """,
            self.conn,
            params=(ticker.upper(),)
        )


    def get_facts(self, ticker):

        return pd.read_sql_query(
            """
            SELECT *
            FROM sec_facts
            WHERE ticker=?
            ORDER BY period_end DESC
            """,
            self.conn,
            params=(ticker.upper(),)
        )


    def get_statements(self, ticker):

        return pd.read_sql_query(
            """
            SELECT *
            FROM sec_statements
            WHERE ticker=?
            ORDER BY created_at DESC
            """,
            self.conn,
            params=(ticker.upper(),)
        )


    # ========================================================
    # CLOSE
    # ========================================================

    def close(self):

        self.conn.close()



# ============================================================
# SEC ANALYSIS REPOSITORY
# ============================================================

class SECAnalysisRepository:

    """
    Repository for secAnalysis.db.

    Stores completed SEC intelligence reports.

    No financial calculations.
    """


    def __init__(self):

        self.conn = sqlite3.connect(
            SEC_ANALYSIS_DB_PATH
        )

        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()

        self.initialize()


    def initialize(self):

        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS analysis_summary(
                ticker TEXT PRIMARY KEY,
                analysis_date TEXT,
                institutional_score REAL,
                growth_asymmetry_score REAL,
                classification TEXT,
                liquidity_score REAL,
                financial_risk TEXT,
                revenue_acceleration TEXT,
                earnings_growth REAL,
                earnings_trend TEXT,
                revenue_cagr_3 REAL,
                revenue_cagr_5 REAL,
                earnings_cagr_3 REAL,
                earnings_cagr_5 REAL,
                growth_quality TEXT,
                growth_quality_score REAL,
                float_category TEXT,
                float_scarcity TEXT,
                dilution_state TEXT,
                float_score REAL,
                share_supply_direction TEXT,
                ownership_trend TEXT,
                dilution_risk TEXT,
                capital_structure TEXT,
                capital_efficiency TEXT,
                allocation_sustainability TEXT,
                capital_allocation_score REAL,
                canslim_classification TEXT,
                canslim_score REAL,
                institutional_sponsorship TEXT,
                json_report TEXT
            )
            """
        )

        self.conn.commit()


    # ========================================================
    # SAVE ANALYSIS
    # ========================================================

    def save_company_analysis(self, ticker, report):

        ticker = ticker.upper().strip()

        earnings = report.get("enhanced_earnings", {})
        annual_growth = report.get("annual_growth", {})
        float_analysis = report.get("float_analysis", {})
        share_structure = report.get("share_structure", {})
        capital = report.get("capital_allocation", {})
        canslim = report.get("canslim", {})
        classification = report.get("classification", {})

        self.cursor.execute(
            """
            INSERT OR REPLACE INTO analysis_summary
            (
                ticker,
                analysis_date,
                institutional_score,
                growth_asymmetry_score,
                classification,
                liquidity_score,
                financial_risk,
                revenue_acceleration,
                earnings_growth,
                earnings_trend,
                revenue_cagr_3,
                revenue_cagr_5,
                earnings_cagr_3,
                earnings_cagr_5,
                growth_quality,
                growth_quality_score,
                float_category,
                float_scarcity,
                dilution_state,
                float_score,
                share_supply_direction,
                ownership_trend,
                dilution_risk,
                capital_structure,
                capital_efficiency,
                allocation_sustainability,
                capital_allocation_score,
                canslim_classification,
                canslim_score,
                institutional_sponsorship,
                json_report
            )
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                ticker,
                report.get("analysis_timestamp"),
                report.get("institutional_score", 0),
                report.get("growth_asymmetry_score", 0),
                classification.get("classification"),
                report.get("liquidity_score", 0),
                report.get("financial_risk", {}).get("risk"),
                report.get("revenue_acceleration", {}).get("state"),
                earnings.get("growth_pct"),
                earnings.get("trend"),
                annual_growth.get("revenue", {}).get("cagr3"),
                annual_growth.get("revenue", {}).get("cagr5"),
                annual_growth.get("earnings", {}).get("cagr3"),
                annual_growth.get("earnings", {}).get("cagr5"),
                annual_growth.get("growth_quality", {}).get("rating"),
                annual_growth.get("growth_quality", {}).get("score"),
                float_analysis.get("float_category"),
                float_analysis.get("float_scarcity"),
                float_analysis.get("dilution_state"),
                float_analysis.get("float_score"),
                share_structure.get("share_supply_direction"),
                share_structure.get("ownership_trend"),
                share_structure.get("dilution_risk"),
                capital.get("structure"),
                capital.get("capital_efficiency"),
                capital.get("allocation_sustainability"),
                capital.get("score"),
                canslim.get("classification"),
                canslim.get("score"),
                canslim.get("institutional"),
                json.dumps(report, default=str)
            )
        )

        self.conn.commit()


    # ========================================================
    # LOAD / QUERY
    # ========================================================

    def load_company_analysis(self, ticker):

        self.cursor.execute(
            """
            SELECT json_report
            FROM analysis_summary
            WHERE ticker=?
            """,
            (ticker.upper(),)
        )

        row = self.cursor.fetchone()

        if row is None:
            return None

        return json.loads(
            row["json_report"]
        )


    def get_analysis(self, ticker):

        self.cursor.execute(
            """
            SELECT *
            FROM analysis_summary
            WHERE ticker=?
            """,
            (ticker.upper(),)
        )

        row = self.cursor.fetchone()

        return dict(row) if row else None


    def fetch_all(self):

        return pd.read_sql_query(
            """
            SELECT *
            FROM analysis_summary
            ORDER BY ticker
            """,
            self.conn
        )


    def search(self, text):

        return pd.read_sql_query(
            """
            SELECT *
            FROM analysis_summary
            WHERE ticker LIKE ?
            ORDER BY ticker
            """,
            self.conn,
            params=(f"%{text.upper()}%",)
        )


    def delete(self, ticker):

        self.cursor.execute(
            """
            DELETE FROM analysis_summary
            WHERE ticker=?
            """,
            (ticker.upper(),)
        )

        self.conn.commit()


    def clear(self):

        self.cursor.execute(
            """
            DELETE FROM analysis_summary
            """
        )

        self.conn.commit()


    def exists(self, ticker):

        self.cursor.execute(
            """
            SELECT 1
            FROM analysis_summary
            WHERE ticker=?
            LIMIT 1
            """,
            (ticker.upper(),)
        )

        return self.cursor.fetchone() is not None


    def count(self):

        self.cursor.execute(
            """
            SELECT COUNT(*)
            FROM analysis_summary
            """
        )

        return self.cursor.fetchone()[0]


    def last_analysis_date(self, ticker):

        self.cursor.execute(
            """
            SELECT analysis_date
            FROM analysis_summary
            WHERE ticker=?
            """,
            (ticker.upper(),)
        )

        row = self.cursor.fetchone()

        return row["analysis_date"] if row else None


    def close(self):

        self.conn.close()        
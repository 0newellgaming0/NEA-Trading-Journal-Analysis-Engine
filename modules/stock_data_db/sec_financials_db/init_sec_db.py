"""
====================================================================
NEA28 SEC FINANCIAL DATABASE INITIALIZER

Module:
    init_sec_db.py


Database:
    secFinancials.db


Purpose
-------
Creates and validates the SEC EDGAR database schema.

Stores:

- SEC company profiles
- SEC filings
- SEC XBRL facts
- SEC financial statements
- SEC ingestion logs


Called by:

modules.stock_data_db.init_db.init_all()


Architecture:

edgartools
      |
      |
sec_edgar_fetcher.py
      |
      |
SECFinancialRepository
      |
      |
secFinancials.db


SQLite is the source of truth.
====================================================================
"""


import os
import sqlite3


from modules.path_resolver import (
    get_sec_financial_db_path
)



# =========================================================
# DATABASE PATH
# =========================================================

SEC_DB_PATH = get_sec_financial_db_path()



# =========================================================
# INITIALIZE SEC DATABASE
# =========================================================


def init_sec_db():

    """
    Creates SEC EDGAR database
    and required tables.
    """


    os.makedirs(
        os.path.dirname(
            SEC_DB_PATH
        ),
        exist_ok=True
    )


    conn = sqlite3.connect(
        SEC_DB_PATH
    )


    conn.execute(
        "PRAGMA journal_mode=WAL"
    )

    conn.execute(
        "PRAGMA foreign_keys=ON"
    )


    cursor = conn.cursor()



    # =====================================================
    # COMPANY MASTER TABLE
    # =====================================================

    cursor.execute(
    """

    CREATE TABLE IF NOT EXISTS sec_company

    (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        ticker TEXT UNIQUE NOT NULL,

        cik TEXT,

        company_name TEXT,

        sic TEXT,

        exchange TEXT,

        industry TEXT,

        created_at TEXT

    )

    """
    )



    # =====================================================
    # SEC FILINGS TABLE
    # =====================================================

    cursor.execute(
    """

    CREATE TABLE IF NOT EXISTS sec_filings

    (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        ticker TEXT NOT NULL,

        accession_number TEXT,

        form TEXT,

        filing_date TEXT,

        report_date TEXT,

        filing_url TEXT,

        document TEXT,

        created_at TEXT,

        UNIQUE(
            ticker,
            accession_number
        ),

        FOREIGN KEY(ticker)
        REFERENCES sec_company(ticker)
        ON UPDATE CASCADE
        ON DELETE CASCADE

    )

    """
    )



    # =====================================================
    # XBRL FACT TABLE
    # =====================================================

    cursor.execute(
    """

    CREATE TABLE IF NOT EXISTS sec_facts
    (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        ticker TEXT NOT NULL,

        concept TEXT,

        label TEXT,

        value REAL,

        numeric_value REAL,

        unit TEXT,

        period_type TEXT,

        period_start TEXT,

        period_end TEXT,

        fiscal_year INTEGER,

        fiscal_period TEXT,

        filing_date TEXT,

        form TEXT,

        accession_number TEXT,

        created_at TEXT,


        FOREIGN KEY(ticker)
        REFERENCES sec_company(ticker)
        ON UPDATE CASCADE
        ON DELETE CASCADE,


        UNIQUE
        (
            ticker,
            concept,
            period_end,
            fiscal_year,
            fiscal_period,
            accession_number,
            form,
            unit
        )

    )

    """
    )

    # =====================================================
    # SEC CONCEPT LIBRARY
    # =====================================================

    cursor.execute(
    """

    CREATE TABLE IF NOT EXISTS concepts
    (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        concept TEXT UNIQUE NOT NULL,

        namespace TEXT,

        label TEXT,

        description TEXT,

        statement_type TEXT,

        created_at TEXT

    )

    """
    )


    # =====================================================
    # SEC CONCEPT KEYWORD INDEX
    # =====================================================

    cursor.execute(
    """

    CREATE TABLE IF NOT EXISTS concept_keywords
    (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        concept TEXT NOT NULL,

        keyword TEXT NOT NULL,

        UNIQUE(
            concept,
            keyword
        )

    )

    """
    )

    # =====================================================
    # FINANCIAL STATEMENT SNAPSHOTS
    # =====================================================

    cursor.execute(
    """

    CREATE TABLE IF NOT EXISTS sec_statements
    (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    ticker TEXT NOT NULL,

    statement_type TEXT,

    fiscal_period TEXT,

    fiscal_year INTEGER,

    period_end TEXT,

    data_json TEXT,

    created_at TEXT,


    FOREIGN KEY(ticker)
    REFERENCES sec_company(ticker)
    ON UPDATE CASCADE
    ON DELETE CASCADE,


    UNIQUE
    (
    ticker,
    statement_type,
    fiscal_year,
    fiscal_period,
    period_end
    )

    )

    """
    )



    # =====================================================
    # SEC INGESTION LOG
    # =====================================================

    cursor.execute(
    """

    CREATE TABLE IF NOT EXISTS sec_ingestion_log

    (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    ticker TEXT NOT NULL,

    action TEXT,

    rows_added INTEGER,

    status TEXT,

    timestamp TEXT,

    FOREIGN KEY(ticker)
    REFERENCES sec_company(ticker)
    ON UPDATE CASCADE
    ON DELETE CASCADE

    )

    """
    )



    # =====================================================
    # INDEXES
    # =====================================================


    indexes = [

        """
        CREATE INDEX IF NOT EXISTS idx_sec_company_ticker
        ON sec_company(ticker)
        """,

        """
        CREATE INDEX IF NOT EXISTS idx_sec_filings_ticker
        ON sec_filings(ticker)
        """,

        """
        CREATE INDEX IF NOT EXISTS idx_sec_filings_form
        ON sec_filings(form)
        """,

        """
        CREATE INDEX IF NOT EXISTS idx_sec_facts_ticker
        ON sec_facts(ticker)
        """,

        """
        CREATE INDEX IF NOT EXISTS idx_sec_facts_concept
        ON sec_facts(concept)
        """,
        
        """
        CREATE INDEX IF NOT EXISTS idx_sec_facts_period
        ON sec_facts(period_end)
        """,


        """
        CREATE INDEX IF NOT EXISTS idx_sec_facts_lookup
        ON sec_facts(
        ticker,
        concept,
        period_end
        )
        """,        
        
        """
        CREATE INDEX IF NOT EXISTS idx_sec_filings_date
        ON sec_filings(filing_date)
        """,

        """
        CREATE INDEX IF NOT EXISTS idx_sec_facts_accession
        ON sec_facts(accession_number)
        """,

        """
        CREATE INDEX IF NOT EXISTS idx_sec_statements_type
        ON sec_statements(statement_type)
        """,

        """
        CREATE INDEX IF NOT EXISTS idx_sec_statements_ticker
        ON sec_statements(ticker)
        """,
        
        """
        CREATE INDEX IF NOT EXISTS idx_concepts_name
        ON concepts(concept)
        """,

        """
        CREATE INDEX IF NOT EXISTS idx_concept_keywords_keyword
        ON concept_keywords(keyword)
        """,

        """
        CREATE INDEX IF NOT EXISTS idx_concept_keywords_concept
        ON concept_keywords(concept)
        """
    ]


    for index in indexes:

        cursor.execute(
            index
        )



    conn.commit()

    conn.close()



    print(
        "SEC Financial Database initialized:",
        SEC_DB_PATH
    )



# =========================================================
# VALIDATION
# =========================================================


def validate_sec_database():
    """
    Confirms required SEC tables and indexes exist.
    """

    required_tables = {

        "sec_company",

        "sec_filings",

        "sec_facts",

        "sec_statements",

        "sec_ingestion_log",
        "concepts",
        "concept_keywords"

    }

    required_indexes = {

        "idx_sec_company_ticker",

        "idx_sec_filings_ticker",
        "idx_sec_filings_form",
        "idx_sec_filings_date",

        "idx_sec_facts_ticker",
        "idx_sec_facts_concept",
        "idx_sec_facts_period",
        "idx_sec_facts_lookup",
        "idx_sec_facts_accession",

        "idx_sec_statements_ticker",
        "idx_sec_statements_type",
        "idx_concepts_name",
        "idx_concept_keywords_keyword",
        "idx_concept_keywords_concept"

    }

    conn = sqlite3.connect(SEC_DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT name
        FROM sqlite_master
        WHERE type='table'
    """)

    existing_tables = {
        row[0]
        for row in cursor.fetchall()
    }

    cursor.execute("""
        SELECT name
        FROM sqlite_master
        WHERE type='index'
    """)

    existing_indexes = {
        row[0]
        for row in cursor.fetchall()
    }

    conn.close()

    missing_tables = required_tables - existing_tables
    missing_indexes = required_indexes - existing_indexes

    if missing_tables:
        print("Missing tables:", sorted(missing_tables))

    if missing_indexes:
        print("Missing indexes:", sorted(missing_indexes))

    return (
        len(missing_tables) == 0
        and
        len(missing_indexes) == 0
    )


# =========================================================
# TEST EXECUTION
# =========================================================

if __name__ == "__main__":


    init_sec_db()


    if validate_sec_database():

        print(
            "SEC database validation PASSED"
        )

    else:

        print(
            "SEC database validation FAILED"
        )
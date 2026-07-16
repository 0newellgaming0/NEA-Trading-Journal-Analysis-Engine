"""
====================================================================
NEA28 SEC CONCEPT LIBRARY

Module:
    sec_concept_library.py

Purpose:
    Dynamic SEC XBRL concept discovery database.

Features:
    - Stores every SEC concept discovered
    - Learns concepts from ticker filings
    - Tracks usage frequency
    - Supports resolver expansion
====================================================================
"""

import sqlite3
import logging
from datetime import datetime

from modules.path_resolver import get_database_path


logger = logging.getLogger("SECConceptLibrary")


DB_PATH = get_database_path(
    "sec_concept_library.db"
)


def initialize():

    conn = sqlite3.connect(DB_PATH)

    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS concepts (

        id INTEGER PRIMARY KEY,

        concept TEXT UNIQUE,

        namespace TEXT,

        taxonomy TEXT,

        first_seen TEXT,

        last_seen TEXT,

        usage_count INTEGER DEFAULT 1,

        category TEXT,

        description TEXT,

        active INTEGER DEFAULT 1
    )
    """)

    conn.commit()
    conn.close()

    logger.info(
        "SEC Concept Library initialized"
    )


def add_concept(
    concept,
    namespace=None,
    taxonomy=None,
    category=None,
    description=None,
):

    now = datetime.utcnow().isoformat()

    conn = sqlite3.connect(DB_PATH)

    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO concepts
    (
        concept,
        namespace,
        taxonomy,
        first_seen,
        last_seen,
        usage_count,
        category,
        description
    )

    VALUES (?,?,?,?,?,?,?,?)

    ON CONFLICT(concept)
    DO UPDATE SET

        last_seen=?,
        usage_count=usage_count+1

    """,
    (
        concept,
        namespace,
        taxonomy,
        now,
        now,
        1,
        category,
        description,
        now,
    ))

    conn.commit()
    conn.close()
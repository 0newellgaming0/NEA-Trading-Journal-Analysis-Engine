"""
====================================================================
NEA28 SEC FINANCIAL INTELLIGENCE SYSTEM

Module:
    shared_utilities.py

Purpose:
    Centralized SEC/XBRL processing utilities shared across all
    NEA28 financial analysis plugins.

Responsibilities:
    - SEC dataframe validation
    - SEC column normalization
    - Numeric value cleaning
    - Concept normalization
    - Dynamic concept resolver interface
    - Duplicate SEC fact resolution
    - Fiscal period validation
    - Growth calculations
    - CAGR calculations
    - Classification helpers
    - Financial history construction
    - Safe plugin outputs
    - Standard logging utilities
    - Plugin dependency access

Design:
    Shared analytical infrastructure only.

    This module does not contain financial domain logic.

    Plugins remain responsible for:
        - Financial interpretation
        - Domain scoring
        - Classification ownership
        - Institutional intelligence

====================================================================
"""

import logging
import math
import pandas as pd


logger = logging.getLogger("SECSharedUtilities")


# ====================================================================
# Data Validation
# ====================================================================

def validate_dataframe(df, required_columns=None):
    if not isinstance(df, pd.DataFrame):
        logger.warning("Invalid dataframe supplied")
        return False

    if required_columns:
        missing = [c for c in required_columns if c not in df.columns]

        if missing:
            logger.warning(
                "Missing dataframe columns: %s",
                missing
            )
            return False

    return True


# ====================================================================
# SEC Normalization
# ====================================================================

def normalize_sec_columns(df):
    if not isinstance(df, pd.DataFrame):
        return df

    rename_map = {
        "Numeric_Value": "numeric_value",
        "Period_End": "period_end",
        "Period_Start": "period_start",
        "Fiscal_Period": "fiscal_period",
        "Fiscal_Year": "fiscal_year",
        "Concept": "concept",
        "Label": "label",
    }

    df = df.rename(columns=rename_map)

    df.columns = [
        str(c).lower()
        for c in df.columns
    ]

    return df


def clean_numeric_values(value):
    if value is None:
        return None

    try:
        if isinstance(value, str):
            value = value.replace(",", "").strip()

        return float(value)

    except Exception:
        return math.nan


def clean_numeric_column(df, column="numeric_value"):
    if column in df.columns:
        df[column] = df[column].apply(
            clean_numeric_values
        )

    return df


# ====================================================================
# SEC Concept Utilities
# ====================================================================

def normalize_concept_name(concept):
    if not concept:
        return ""

    return str(concept).split(":")[-1]


def normalize_concepts(df):
    if "concept" in df.columns:
        df["concept"] = df["concept"].apply(
            normalize_concept_name
        )

    return df


def resolve_plugin_concepts(concept_keys, resolver):
    if not resolver:
        return []

    try:
        return resolver.resolve(
            concept_keys
        )

    except Exception:
        logger.exception(
            "Concept resolution failed"
        )
        return []


# ====================================================================
# SEC Duplicate Fact Resolution
# ====================================================================

def resolve_duplicate_facts(
    df,
    priority_list
):
    if df.empty:
        return df

    if "concept" not in df.columns:
        return df

    priority_map = {
        concept: index
        for index, concept in enumerate(priority_list)
    }

    df["_priority"] = df["concept"].map(
        priority_map
    ).fillna(
        len(priority_map)
    )

    sort_columns = [
        "_priority"
    ]

    if "period_end" in df.columns:
        sort_columns.append(
            "period_end"
        )

    df = df.sort_values(
        sort_columns
    )

    subset = [
        "period_end"
    ]

    if "fiscal_period" in df.columns:
        subset.append(
            "fiscal_period"
        )

    df = df.drop_duplicates(
        subset=subset,
        keep="first"
    )

    return df.drop(
        columns=["_priority"],
        errors="ignore"
    )


# ====================================================================
# SEC Period Validation
# ====================================================================

def validate_quarter_period(days):
    return 70 <= days <= 110


def validate_annual_period(days):
    return 330 <= days <= 380


def filter_reporting_periods(
    df,
    period_type
):
    if df.empty:
        return df

    if "fiscal_period" not in df.columns:
        return df

    return df[
        df["fiscal_period"] == period_type
    ]


# ====================================================================
# Fiscal Matching
# ====================================================================

def find_prior_period(
    history,
    year,
    period
):
    target_year = year - 1

    for item in history:
        if (
            item.get("year") == target_year
            and item.get("period") == period
        ):
            return item

    return None


def find_previous_quarter(
    history,
    year,
    period_order
):
    current_index = period_order.index(
        year
    )

    if current_index == 0:
        return None

    return history[current_index - 1]


# ====================================================================
# Financial Math
# ====================================================================

def calculate_growth(
    current,
    previous
):
    if previous in (None, 0):
        return 0.0

    try:
        return (
            (current - previous)
            /
            abs(previous)
        ) * 100

    except Exception:
        return 0.0


def calculate_cagr(
    start,
    end,
    years
):
    if start <= 0 or years <= 0:
        return 0.0

    try:
        return (
            (
                end / start
            ) ** (1 / years)
            - 1
        ) * 100

    except Exception:
        return 0.0


# ====================================================================
# Classification
# ====================================================================

def classify_growth(value):
    if value >= 15:
        return "STRONG UP"

    if value >= 5:
        return "UP"

    if value <= -15:
        return "STRONG DOWN"

    if value <= -5:
        return "DOWN"

    return "STABLE"


def classify_score(value):
    if value >= 90:
        return "EXCELLENT"

    if value >= 75:
        return "GOOD"

    if value >= 50:
        return "AVERAGE"

    if value >= 25:
        return "WEAK"

    return "POOR"


# ====================================================================
# History Utilities
# ====================================================================

def build_financial_history(records):
    history = []

    for item in records:
        history.append(
            {
                "year": item.get("year"),
                "period": item.get("period"),
                "value": item.get("value"),
            }
        )

    return history


# ====================================================================
# Plugin Output Utilities
# ====================================================================

def empty_plugin_output(plugin=None):
    return {
        "plugin": plugin or "",
        "metrics": {},
        "history": [],
        "scores": {},
        "classification": "UNKNOWN",
        "metadata": {},
    }


def get_plugin_output(
    analysis,
    plugin_name
):
    if not isinstance(
        analysis,
        dict
    ):
        return {}

    return analysis.get(
        plugin_name,
        {}
    )


# ====================================================================
# Logging Utilities
# ====================================================================

def log_plugin_header(name):
    logger.info(
        "=" * 70
    )
    logger.info(
        name.upper()
    )
    logger.info(
        "=" * 70
    )


def log_metric_block(
    metric,
    value,
    classification=None
):
    logger.info(
        "%s : %s",
        metric,
        value
    )

    if classification:
        logger.info(
            "Classification : %s",
            classification
        )
        
def find_first_available_concept(
    df,
    concept_priority
):

    if df.empty:
        return {
            "concept": None,
            "records": df.iloc[0:0]
        }

    if isinstance(concept_priority, str):
        concept_priority = [
            concept_priority
        ]

    for concept in concept_priority:

        clean = normalize_concept_name(
            concept
        )

        matches = df[
            df["concept"] == clean
        ]

        if not matches.empty:
            logger.info(
                "Selected SEC concept: %s",
                clean
            )

            return {
                "concept": clean,
                "records": matches
            }

    logger.warning(
        "No available concepts found. Tried: %s",
        concept_priority
    )

    return {
        "concept": None,
        "records": df.iloc[0:0]
    }
    
def resolve_priority_concepts(
    key,
    resolver
):

    concepts = resolver.resolve(
        key
    )

    if isinstance(concepts,str):
        return [
            concepts
        ]

    return concepts    
    
def get_sec_concepts(category, metric):

    registry = SEC_REGISTRIES.get(category)

    if not registry:
        return []

    concepts = registry.get(metric, [])

    if isinstance(concepts, str):
        concepts = [concepts]

    return concepts    
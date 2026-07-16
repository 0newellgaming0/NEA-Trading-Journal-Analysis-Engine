"""
====================================================================
NEA28 SHARE STRUCTURE ENGINE

Module:
    share_structure.py

Purpose:
    Institutional SEC XBRL share supply analysis.

Features:
    - Shares outstanding analysis
    - Share count change detection
    - Buyback detection
    - Dilution detection
    - Treasury stock analysis
    - Supply pressure scoring

Used By:
    SECAnalysis
    CANSLIM Engine
    Institutional Accumulation Engine
    Growth Asymmetry Engine
====================================================================
"""

from __future__ import annotations

import yfinance as yf
import logging
import pandas as pd
from modules.stock_data_db.sec_financials_db.sec_concept_resolver import (
    resolve_concepts,
    resolve_by_keywords,
)

logger = logging.getLogger("ShareStructure")
        
def _normalize_concept(value):

    if not isinstance(value, str):
        return ""

    return value.split(":")[-1].strip()


def _log_sec_source(prepared):

    if prepared.empty:
        return

    logger.info(
        "SEC Share Structure Input"
    )

    logger.info(
        "Rows received: %s",
        len(prepared)
    )

    logger.info(
        "Unique concepts received: %s",
        prepared["normalized_concept"].nunique()
    )

    logger.info(
        "Sample concepts: %s",
        sorted(
            prepared["normalized_concept"]
            .unique()
        )[:25]
    )
    
def _prepare_dataframe(df: pd.DataFrame) -> pd.DataFrame:

    if df is None or df.empty:
        return pd.DataFrame()

    data = df.copy()

    data.columns = [
        str(column).strip().lower()
        for column in data.columns
    ]

    required_columns = [
        "concept",
        "numeric_value",
        "period_end",
        "fiscal_year",
        "fiscal_period",
    ]

    for column in required_columns:

        if column not in data.columns:
            logger.warning("Missing SEC column: %s", column)
            return pd.DataFrame()

    data["normalized_concept"] = data["concept"].astype(str).apply(
        _normalize_concept
    )

    data["numeric_value"] = pd.to_numeric(
        data["numeric_value"],
        errors="coerce",
    )

    data["fiscal_year"] = pd.to_numeric(
        data["fiscal_year"],
        errors="coerce",
    )

    data["period_end"] = pd.to_datetime(
        data["period_end"],
        errors="coerce",
    )

    data = data.dropna(
        subset=[
            "numeric_value",
            "period_end",
            "fiscal_year",
            "fiscal_period",
        ]
    )

    return data


def _extract_concept_rows(prepared_df: pd.DataFrame, canonical_concept: str) -> pd.DataFrame:

    if prepared_df.empty:
        return pd.DataFrame()

    aliases = resolve_concepts(canonical_concept)

    if not aliases:
        logger.warning(
            "No SEC registry aliases defined for canonical concept '%s'",
            canonical_concept,
        )
        return pd.DataFrame()

    rows = prepared_df[
        prepared_df["normalized_concept"].isin(aliases)
    ].copy()

    logger.debug(
        "Canonical=%s | Aliases=%d | Matches=%d",
        canonical_concept,
        len(aliases),
        len(rows),
    )

    if rows.empty:
        logger.debug(
            "No SEC rows matched canonical concept '%s'",
            canonical_concept,
        )
        return pd.DataFrame()

    return rows.sort_values(
        [
            "fiscal_year",
            "period_end",
        ]
    )


def _latest_row(df):

    if df.empty:
        return None

    return df.sort_values(
        [
            "fiscal_year",
            "period_end",
        ],
        ascending=False,
    ).iloc[0]

def _select_best_concept_row(
    df,
    preferred
):

    if df.empty:
        return None


    for concept in preferred:

        match = df[
            df["normalized_concept"] == concept
        ]

        if not match.empty:
            return _latest_row(match)


    return _latest_row(df)
    
def _previous_year_row(df):

    if df.empty:
        return None

    latest = _latest_row(df)

    previous = df[
        df["fiscal_year"]
        ==
        latest["fiscal_year"] - 1
    ]

    if previous.empty:
        return None

    return previous.sort_values(
        "period_end",
        ascending=False,
    ).iloc[0]

def _extract_dynamic_concepts(
    prepared_df,
    keywords,
    exclude=None,
):

    if prepared_df.empty:
        return pd.DataFrame()

    concepts = resolve_by_keywords(
        keywords
    )

    if not concepts:
        logger.warning(
            "No concepts resolved for keywords=%s",
            keywords,
        )
        return pd.DataFrame()

    concepts = {
        _normalize_concept(concept)
        for concept in concepts
    }

    rows = prepared_df[
        prepared_df["normalized_concept"].isin(concepts)
    ].copy()


    if exclude:

        exclude_pattern = "|".join(exclude)

        rows = rows[
            ~rows["normalized_concept"]
            .str.contains(
                exclude_pattern,
                case=False,
                regex=True,
                na=False,
            )
        ]


    logger.info(
        "Dynamic concept search | keywords=%s | resolved=%s | matches=%s",
        keywords,
        list(concepts),
        len(rows),
    )

    return rows
    
class ShareStructure:


    def _get_close_price(self, ticker):

        if not ticker:
            return None

        try:
            stock = yf.Ticker(ticker)

            # Fast path
            try:
                info = stock.fast_info

                close_price = (
                    info.get("lastPrice")
                    or info.get("previousClose")
                    or info.get("regularMarketPreviousClose")
                )

                if close_price is not None:
                    close_price = float(close_price)

                    return close_price

            except Exception:
                logger.debug("fast_info unavailable")

            # Fallback to history
            history = stock.history(
                period="5d",
                auto_adjust=False,
            )

            if not history.empty:

                history = history.dropna(subset=["Close"])

                if not history.empty:

                    close_price = float(history["Close"].iloc[-1])

                    logger.info(
                        "Yahoo historical close (%s): %.2f",
                        ticker,
                        close_price,
                    )

                    return close_price

        except Exception:
            logger.exception(
                "Unable to retrieve Yahoo close price for %s",
                ticker,
            )

        return None

        
    def analyze(self, df: pd.DataFrame, ticker=None):

        report = {
            "ticker": ticker,
            "current_shares": None,
            "previous_shares": None,
            "current_share_change_pct": None,
            "capital_base_trend": "UNKNOWN",
            "share_supply_direction": "UNKNOWN",
            "six_month_change_pct": None,
            "one_year_change_pct": None,
            "issuance_pressure": "UNKNOWN",
            "buyback_support": "UNKNOWN",
            "buyback_detected": False,
            "dilution_detected": False,
            "net_share_impact": "UNKNOWN",
            "buyback_value": 0,
            "buyback_yield": None,
            "issuance_value": 0,
            "issued_shares": 0,
            "dilution_rate": None,
            "treasury_stock": 0,
            "treasury_stock_shares": 0,
            "treasury_stock_value": 0,
            "treasury_stock_cost": 0,
            "close_price": None,
            "market_cap": None,
            "share_based_compensation": "UNKNOWN",
            "management_alignment": "UNKNOWN",
            "supply_impact": "UNKNOWN",
            "ownership_trend": "UNKNOWN",
            "dilution_risk": "UNKNOWN",
            "capital_quality": "UNKNOWN",
            "three_year_cagr": None,
            "five_year_cagr": None,
            "historical_trend": "UNKNOWN",
            "public_float": None,
            "float_category": "UNKNOWN",
            "supply_score": 0,
            "buyback_offset_dilution": "UNKNOWN",
        }

        try:

            if isinstance(df, list):
                df = pd.DataFrame(df)

            if not isinstance(df, pd.DataFrame):
                logger.error("ShareStructure expects DataFrame")
                return report

            prepared = _prepare_dataframe(df)

            _log_sec_source(prepared)

            if prepared.empty:
                logger.error("No SEC data available for share structure analysis")
                return report

            shares = _extract_concept_rows(prepared, "COMMON_SHARES_OUTSTANDING")
            issued = _extract_concept_rows(prepared, "SHARES_ISSUED")
            weighted_diluted = _extract_concept_rows(prepared, "WEIGHTED_DILUTED")

            repurchased_shares = _extract_concept_rows(prepared, "REPURCHASED_SHARES")
            repurchased_value = _extract_concept_rows(prepared, "REPURCHASED_VALUE")

            share_comp = _extract_concept_rows(prepared, "SHARE_BASED_COMPENSATION")
            allocated_comp = _extract_concept_rows(prepared, "ALLOCATED_SHARE_COMPENSATION")

            treasury_shares = _extract_concept_rows(
                prepared,
                "TREASURY_SHARES"
            )

            treasury_value = _extract_concept_rows(
                prepared,
                "TREASURY_STOCK_VALUE"
            )

            treasury_cost = _extract_concept_rows(
                prepared,
                "TREASURY_STOCK_COST"
            )
            
            logger.info(
                "Treasury concept rows | Shares=%s Value=%s Cost=%s",
                len(treasury_shares),
                len(treasury_value),
                len(treasury_cost),
            )
            public_float = _extract_concept_rows(prepared, "PUBLIC_FLOAT")

            latest = _latest_row(shares)

            if latest is not None:

                current = float(latest["numeric_value"])
                report["current_shares"] = current

                close_price = self._get_close_price(ticker)
                report["close_price"] = close_price

                if close_price:
                    report["market_cap"] = current * close_price

                previous = _previous_year_row(shares)

                if previous is not None:

                    prior = float(previous["numeric_value"])
                    report["previous_shares"] = prior

                    if prior > 0:

                        change = ((current - prior) / prior) * 100

                        report["current_share_change_pct"] = change
                        report["one_year_change_pct"] = change

                        if change < 0:
                            report["capital_base_trend"] = "SHRINKING"
                            report["share_supply_direction"] = "CONTRACTING"
                        elif change > 0:
                            report["capital_base_trend"] = "EXPANDING"
                            report["share_supply_direction"] = "INCREASING"
                        else:
                            report["capital_base_trend"] = "STABLE"
                            report["share_supply_direction"] = "NEUTRAL"

            if not shares.empty:

                latest_date = shares["period_end"].max()

                six_month_rows = shares[
                    shares["period_end"] <= latest_date - pd.DateOffset(months=6)
                ]

                if not six_month_rows.empty:

                    six_month = six_month_rows.sort_values("period_end").iloc[-1]
                    six_value = float(six_month["numeric_value"])

                    if six_value > 0:

                        report["six_month_change_pct"] = (
                            (report["current_shares"] - six_value)
                            / six_value
                        ) * 100

            if not repurchased_value.empty:

                latest_buyback = _latest_row(repurchased_value)

                if latest_buyback is not None:
                    report["buyback_value"] = abs(float(latest_buyback["numeric_value"]))

                if report["market_cap"]:
                    report["buyback_yield"] = (
                        report["buyback_value"] / report["market_cap"]
                    ) * 100

                if (
                    report["buyback_value"] > 0
                    and not repurchased_shares.empty
                ):

                    report["buyback_detected"] = True
                    report["buyback_support"] = "POSITIVE"

            if not issued.empty:

                latest_issued = _latest_row(issued)

                if latest_issued is not None:

                    issued_shares = float(latest_issued["numeric_value"])
                    report["issued_shares"] = issued_shares

                    previous_issued = _previous_year_row(issued)

                    if previous_issued is not None:

                        previous_value = float(previous_issued["numeric_value"])
                        new_issuance = issued_shares - previous_value

                        if new_issuance > 0:

                            report["issuance_value"] = new_issuance
                            report["dilution_detected"] = True
                            report["issuance_pressure"] = "INCREASING"

                            if report["current_shares"]:
                                report["dilution_rate"] = (
                                    new_issuance / report["current_shares"]
                                ) * 100

                        else:
                            report["issuance_value"] = 0
                            report["dilution_rate"] = 0
                            report["issuance_pressure"] = "NONE"

            if (
                not weighted_diluted.empty
                and not shares.empty
            ):

                diluted = float(
                    _latest_row(weighted_diluted)["numeric_value"]
                )

                current = report.get("current_shares")

                if current and diluted > current:

                    dilution_pct = (
                        (diluted - current)
                        /
                        current
                    ) * 100

                    if dilution_pct > 2:

                        report["dilution_detected"] = True
                        report["dilution_rate"] = dilution_pct

            share_change = report.get("six_month_change_pct")

            if share_change is not None:

                if share_change > 10:
                    report["dilution_risk"] = "HIGH"

                elif share_change > 3:
                    report["dilution_risk"] = "MODERATE"

                elif share_change > 0.25:
                    report["dilution_risk"] = "LOW"

                else:
                    report["dilution_risk"] = "NONE"

            elif report["dilution_detected"]:

                report["dilution_risk"] = "UNKNOWN"

            else:

                report["dilution_risk"] = "NONE"
                
            if not treasury_shares.empty:
                report["treasury_stock_shares"] = abs(
                    treasury_shares["numeric_value"].astype(float).sum()
                )

            if not treasury_value.empty:
                report["treasury_stock_value"] = abs(
                    treasury_value["numeric_value"].astype(float).sum()
                )

            if not treasury_cost.empty:
                report["treasury_stock_cost"] = abs(
                    treasury_cost["numeric_value"].astype(float).sum()
                )

            report["treasury_stock"] = {
                "shares": report["treasury_stock_shares"],
                "value": report["treasury_stock_value"],
                "cost": report["treasury_stock_cost"],
            }

            comp_value = 0.0

            for comp_df in (
                share_comp,
                allocated_comp,
            ):
                if not comp_df.empty:
                    comp_value += abs(
                        comp_df["numeric_value"].astype(float).sum()
                    )

            if comp_value > 0:
                report["share_based_compensation"] = "ELEVATED"
            else:
                report["share_based_compensation"] = "LOW"

            if not public_float.empty:

                latest_float = _latest_row(public_float)

                if latest_float is not None:
                    report["public_float"] = float(latest_float["numeric_value"])
                    self._classify_float(report)

            current_change = report.get("current_share_change_pct")
            buyback_offset = False

            if (
                report["buyback_detected"]
                and report["issuance_value"] > 0
                and report["buyback_value"] > 0
            ):
                buyback_offset = current_change <= 0

            if current_change is not None:

                # --------------------------------------------------
                # Ownership trend
                # --------------------------------------------------

                if current_change < -0.25:
                    report["ownership_trend"] = "SHARE BASE SHRINKING"

                elif current_change > 0.25:
                    report["ownership_trend"] = "SHARE BASE EXPANDING"

                else:
                    report["ownership_trend"] = "STABLE SHARE BASE"

                # --------------------------------------------------
                # Supply impact
                # --------------------------------------------------

                if current_change < -0.25:
                    report["supply_impact"] = "FAVORABLE"

                elif current_change > 0.25:
                    report["supply_impact"] = "NEGATIVE"

                else:
                    report["supply_impact"] = "NEUTRAL"

                # --------------------------------------------------
                # Net capital allocation
                # --------------------------------------------------

                if current_change < 0:

                    report["net_share_impact"] = "ACCRETIVE"
                    report["capital_quality"] = "ACCRETIVE"

                elif buyback_offset:

                    report["net_share_impact"] = "OFFSETTING DILUTION"
                    report["capital_quality"] = "NEUTRAL"

                else:

                    report["net_share_impact"] = "DILUTIVE"
                    report["capital_quality"] = "DILUTIVE"
                    
            if report["buyback_detected"]:

                if current_change is not None and current_change <= 0:

                    report["buyback_offset_dilution"] = "FULL"

                elif current_change is not None and current_change > 0:

                    report["buyback_offset_dilution"] = "PARTIAL"

                else:

                    report["buyback_offset_dilution"] = "UNKNOWN"     

            report["three_year_cagr"] = self._calculate_share_cagr(shares, 3)
            report["five_year_cagr"] = self._calculate_share_cagr(shares, 5)

            if report["three_year_cagr"] is not None:

                if report["three_year_cagr"] < 0:
                    report["historical_trend"] = "CONSISTENT SHARE REDUCTION"
                elif report["three_year_cagr"] > 0:
                    report["historical_trend"] = "CONSISTENT SHARE EXPANSION"
                else:
                    report["historical_trend"] = "STABLE SHARE COUNT"               

            share_cagr = report.get("three_year_cagr")

            if report["net_share_impact"] == "ACCRETIVE":

                report["management_alignment"] = "SHAREHOLDER FRIENDLY"

            elif report["buyback_offset_dilution"] == "FULL":

                report["management_alignment"] = "SHAREHOLDER FRIENDLY"

            elif (
                share_cagr is not None
                and share_cagr > 2
            ):

                report["management_alignment"] = "SHAREHOLDER DILUTIVE"

            else:

                report["management_alignment"] = "NEUTRAL"

            report["supply_score"] = self._calculate_supply_score(report)

            self._log_report(report)

        except Exception:
            logger.exception("Share structure analysis failed")

        return report

    def _calculate_share_cagr(self, shares, years):
        if shares.empty:
            return None

        latest = _latest_row(shares)

        if latest is None:
            return None

        current = float(
            latest["numeric_value"]
        )

        target_year = (
            latest["fiscal_year"]
            -
            years
        )

        historical = shares[
            shares["fiscal_year"] <= target_year
        ]

        if historical.empty:
            return None

        previous = historical.sort_values(
            [
                "fiscal_year",
                "period_end",
            ],
            ascending=False,
        ).iloc[0]

        starting_value = float(
            previous["numeric_value"]
        )

        if starting_value <= 0 or current <= 0:
            return None

        cagr = (
            (
                current
                /
                starting_value
            )
            **
            (1 / years)
            -
            1
        ) * 100

        return cagr
        
    def _classify_float(self, report):

        float_value = report.get("public_float")

        if float_value is None:
            return

        if float_value < 20_000_000:
            report["float_category"] = "MICRO FLOAT"

        elif float_value < 50_000_000:
            report["float_category"] = "LOW FLOAT"

        elif float_value < 150_000_000:
            report["float_category"] = "MEDIUM FLOAT"

        elif float_value < 500_000_000:
            report["float_category"] = "LARGE FLOAT"

        else:
            report["float_category"] = "MEGA FLOAT"


    def _calculate_supply_score(self, report):

        score = 50

        if report.get("buyback_detected"):
            score += 25

        if report.get("dilution_detected"):
            score -= 30

        float_value = report.get("public_float")

        if float_value is not None:

            if float_value < 50_000_000:
                score += 15

            elif float_value > 500_000_000:
                score -= 10

        return max(0, min(100, score))
        
    def _safe_percent(self, value):
        if value is None:
            return 0.0

        try:
            return float(value)

        except (TypeError, ValueError):
            return 0.0        

    def _log_report(self, report):

        def pct(value):
            return float(value) if value is not None else 0.0

        logger.info("=" * 70)
        logger.info("SHARE STRUCTURE ANALYSIS")
        logger.info("=" * 70)

        logger.info("CURRENT CAPITAL STRUCTURE")
        logger.info("-" * 70)
        logger.info("Market Capitalization    : %s", report.get("market_cap"))
        logger.info("Close Price              : %s", report.get("close_price"))        
        logger.info("Shares Outstanding       : %s", report.get("current_shares"))
        logger.info("Previous Period Shares   : %s", report.get("previous_shares"))
        logger.info("Current Share Change     : %.2f%%", pct(report.get("current_share_change_pct")))
        logger.info("Capital Base Trend       : %s", report.get("capital_base_trend"))
        logger.info("Share Supply Direction   : %s", report.get("share_supply_direction"))

        logger.info("SHORT-TERM SHARE TREND")
        logger.info("-" * 70)
        logger.info("6 Month Share Change     : %.2f%%", pct(report.get("six_month_change_pct")))
        logger.info("1 Year Share Change      : %.2f%%", pct(report.get("one_year_change_pct")))
        logger.info("Recent Issuance Pressure : %s", report.get("issuance_pressure"))
        logger.info("Recent Buyback Support   : %s", report.get("buyback_support"))
        logger.info("Net Share Impact         : %s", report.get("net_share_impact"))

        logger.info("CAPITAL ALLOCATION")
        logger.info("-" * 70)
        logger.info("Current Buyback Value    : %s", report.get("buyback_value"))
        logger.info("Buyback Yield            : %.2f%%", pct(report.get("buyback_yield")))
        logger.info("Current Issuance Value   : %s", report.get("issuance_value"))
        logger.info("Dilution Rate            : %.2f%%", pct(report.get("dilution_rate")))

        logger.info("EQUITY MANAGEMENT")
        logger.info("-" * 70)
        logger.info(
            "Treasury Shares           : %s",
            report.get("treasury_stock_shares")
        )

        logger.info(
            "Treasury Value            : %s",
            report.get("treasury_stock_value")
        )

        logger.info(
            "Treasury Cost             : %s",
            report.get("treasury_stock_cost")
        )
        logger.info("Share Based Compensation : %s", report.get("share_based_compensation"))
        logger.info("Management Alignment     : %s", report.get("management_alignment"))

        logger.info("INSTITUTIONAL ASSESSMENT")
        logger.info("-" * 70)
        logger.info("Supply Impact            : %s", report.get("supply_impact"))
        logger.info("Ownership Trend          : %s", report.get("ownership_trend"))
        logger.info("Dilution Risk            : %s", report.get("dilution_risk"))
        logger.info("Capital Quality          : %s", report.get("capital_quality"))

        logger.info("LONG-TERM CONTEXT")
        logger.info("-" * 70)
        logger.info("3 Year Share CAGR        : %.2f%%", pct(report.get("three_year_cagr")))
        logger.info("5 Year Share CAGR        : %.2f%%", pct(report.get("five_year_cagr")))
        logger.info("Historical Trend         : %s", report.get("historical_trend"))

        logger.info("=" * 70)
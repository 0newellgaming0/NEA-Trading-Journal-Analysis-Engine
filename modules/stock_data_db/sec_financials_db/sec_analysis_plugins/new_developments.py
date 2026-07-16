"""
====================================================================
NEA28 NEW DEVELOPMENTS ENGINE

Module:
    new_developments.py

Purpose
-------
Institutional SEC filing intelligence engine for CANSLIM "N" analysis.

Analyzes SEC filing documents for:

- New Products
- New Technology
- AI Initiatives
- Strategic Partnerships
- Major Contracts
- Market Expansion
- Manufacturing Expansion
- Acquisitions
- Management Changes
- Business Transformation

Architecture

SEC Database
      │
      ▼
SECFinancialRepository
      │
      ▼
NewDevelopmentsEngine
      ├── Query filing metadata
      ├── Build SEC document URLs
      ├── Download selected filing documents
      ├── Extract filing text
      ├── Search institutional catalysts
      ├── Score CANSLIM N
      ▼
SECAnalysisExtensions
      ▼
CANSLIM Engine

Notes
-----
Uses SEC filing metadata already stored by SECFetcher.
Does NOT perform SEC ingestion, XBRL downloads, company updates,
or database population.

====================================================================
"""

from __future__ import annotations

import logging
import re

import pandas as pd
import requests

from bs4 import BeautifulSoup

from modules.stock_data_db.sec_financials_db.sec_repository import (
    SECFinancialRepository,
)
from modules.path_resolver import (
    get_sec_financial_db_path,
)

logger = logging.getLogger("NewDevelopments")

NEW_PRODUCT_KEYWORDS = [
    "new product","new service","product launch","launched",
    "introduced","released","commercial launch",
    "general availability","rollout","platform launch",
]

AI_KEYWORDS = [
    "artificial intelligence","ai","machine learning",
    "generative ai","large language model",
    "foundation model","copilot","automation",
]

TECHNOLOGY_KEYWORDS = [
    "new technology","innovation","technology platform",
    "proprietary technology","patent",
    "intellectual property",
]

PARTNERSHIP_KEYWORDS = [
    "strategic partnership","strategic alliance",
    "collaboration","joint venture",
    "agreement","partnered",
]

CONTRACT_KEYWORDS = [
    "contract award","customer agreement",
    "multi-year agreement","purchase agreement",
    "government contract","long-term contract",
]

EXPANSION_KEYWORDS = [
    "expansion","new facility","new manufacturing",
    "new factory","capacity expansion",
    "production expansion","new market",
    "international expansion",
]

ACQUISITION_KEYWORDS = [
    "acquisition","acquired","merger",
    "strategic investment","business combination",
]

MANAGEMENT_KEYWORDS = [
    "appointed chief executive",
    "appointed ceo",
    "appointed cfo",
    "new chief executive",
    "leadership change",
    "management transition",
]


class NewDevelopmentsEngine:

    def __init__(self):

        self.repository = SECFinancialRepository()

        # Used only to retrieve individual filing documents
        # selected from sec_filings.
        self.session = requests.Session()

        self.session.headers.update({

            "User-Agent":
                "Newell Trading Group research@example.com",

            "Accept":
                "text/html,application/xhtml+xml",

            "Accept-Language":
                "en-US,en;q=0.9",

        })

        logger.info(
            "New Developments Engine initialized"
        )

    def analyze(self, df: pd.DataFrame):

        report = self._empty_report()

        try:

            if df.empty:
                return report

            ticker = (
                str(df.iloc[0]["ticker"])
                .upper()
                .strip()
            )

            logger.info(
                "Running New Developments Analysis: %s",
                ticker
            )

            logger.info("-"*70)
            report["ticker"] = ticker

            filings = self._get_recent_filings(
                ticker=ticker
            )

            if filings.empty:
                logger.info(
                    "No qualifying SEC filings found for %s",
                    ticker
                )
                return self._empty_report()

            cik = self._get_company_cik(
                ticker
            )

            if not cik:
                logger.warning(
                    "Unable to locate CIK for %s",
                    ticker
                )
                return self._empty_report()

            report = {
                "ticker": ticker,
                "filings_reviewed": [],
                "events": [],
                "new_products": 0,
                "ai_mentions": 0,
                "technology_mentions": 0,
                "partnerships": 0,
                "contracts": 0,
                "expansions": 0,
                "acquisitions": 0,
                "management_changes": 0,
            }

            for _, filing in filings.iterrows():

                document_url = self._build_document_url(
                    cik=cik,
                    accession_number=filing.get("accession_number"),
                    primary_document=filing.get("document"),
                )

                if not document_url:
                    continue

                filing_text = self._fetch_filing_document(
                    document_url
                )

                if not filing_text:
                    continue

                events, counts = self._scan_filing_text(
                    filing_text=filing_text,
                    filing=filing
                )

                report["events"].extend(events)

                for key, value in counts.items():
                    report[key] += value

                report["filings_reviewed"].append({
                    "form": filing.get("form"),
                    "date": filing.get("filing_date"),
                    "accession_number": filing.get("accession_number"),
                    "document": filing.get("document"),
                    "url": document_url,
                })

            report.update(
                self._score_n_component(
                    report
                )
            )

            self._log_report(
                report
            )

            return report

        except Exception:
            logger.exception(
                "New Developments Analysis failed"
            )

            report.update({
                "innovation_state": "UNKNOWN",
                "strategic_momentum": "UNKNOWN",
                "catalyst_score": 0,
                "score": 0,
                "quality": "FAILED",
                "error": True,
            })

            return report

    def _get_company_cik(self,ticker):
        try:
            import json
            from pathlib import Path

            metadata_path = (
                Path(
                    get_sec_financial_db_path()
                ).parent
                / "sec_financials_db"
                / "financials"
                / "SEC"
                / ticker.upper().strip()
                / "metadata.json"
            )

            if not metadata_path.exists():
                logger.warning(
                    "SEC metadata file not found: %s",
                    metadata_path
                )
                return None

            with open(
                metadata_path,
                "r",
                encoding="utf-8"
            ) as file:
                metadata = json.load(file)

            metadata_ticker = (
                str(metadata.get("ticker",""))
                .upper()
                .strip()
            )

            if metadata_ticker != ticker.upper().strip():
                logger.warning(
                    "Metadata ticker mismatch: %s != %s",
                    metadata_ticker,
                    ticker
                )
                return None

            cik = metadata.get("cik")

            if cik is None:
                logger.warning(
                    "Metadata CIK missing for ticker: %s",
                    ticker
                )
                return None

            cik = (
                str(cik)
                .replace("CIK","")
                .strip()
                .lstrip("0")
            )

            return cik

        except Exception:
            logger.exception(
                "Unable to retrieve SEC metadata CIK: %s",
                ticker
            )
            return None

    def _get_recent_filings(self,ticker,forms=("8-K","10-Q","10-K"),limit=10):
        try:

            filings = pd.read_sql_query(
                """
                SELECT *
                FROM sec_filings
                WHERE ticker = ?
                ORDER BY filing_date DESC
                """,
                self.repository.conn,
                params=(
                    ticker.upper().strip(),
                )
            )

            if filings.empty:
                logger.warning(
                    "No filings found for ticker: %s",
                    ticker
                )
                return pd.DataFrame()

            if "form" not in filings.columns:
                logger.error(
                    "Missing required 'form' column"
                )
                return pd.DataFrame()

            filings = filings[
                filings["form"].isin(forms)
            ].copy()

            if filings.empty:
                logger.warning(
                    "No qualifying filings after form filtering"
                )
                return pd.DataFrame()

            if "filing_date" not in filings.columns:
                logger.error(
                    "Missing required 'filing_date' column"
                )
                return pd.DataFrame()

            filings = filings.sort_values(
                "filing_date",
                ascending=False
            )

            return filings.head(
                limit
            ).reset_index(drop=True)

        except Exception:
            logger.exception(
                "Unable to retrieve SEC filings: %s",
                ticker
            )
            return pd.DataFrame()

    def _build_document_url(self,cik,accession_number,primary_document):
        if not cik or not accession_number or not primary_document:
            return None
        cik=str(cik).replace("CIK","").lstrip("0")
        accession=str(accession_number).replace("-","")
        return f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession}/{primary_document}"

    def _fetch_filing_document(self, url):

        if not url:
            return ""

        try:

            logger.info(
                "Filings : %s",
                url
            )

            response = self.session.get(
                url,
                timeout=20,
            )          

            response.raise_for_status()

            return self._clean_html(
                response.text
            )


        except Exception:

            logger.exception(
                "Unable to retrieve filing document: %s",
                url
            )

            return ""



    def _clean_html(self, html):
        try:
            soup = BeautifulSoup(html, "html.parser")
            for tag in soup(["script", "style", "noscript"]):
                tag.decompose()
            text = soup.get_text(separator=" ")
            text = re.sub(r"\s+", " ", text)
            return text.lower().strip()
        except Exception:
            logger.exception("HTML cleanup failed")
            return ""

    def _extract_candidate_sentences(self, filing_text):

        excluded_sections = [
            "risk factors",
            "forward-looking statements",
            "legal proceedings",
            "market risk",
            "commitments and contingencies",
            "unresolved staff comments",
            "quantitative and qualitative disclosures about market risk",
        ]

        sentences = re.split(
            r"(?<=[.!?])\s+",
            filing_text
        )

        candidates = []

        for sentence in sentences:

            sentence = sentence.strip().lower()

            if len(sentence) < 40:
                continue

            if any(
                section in sentence
                for section in excluded_sections
            ):
                continue

            candidates.append(sentence)

        return candidates


    def _classify_event(self, sentence):

        classifications = [

            (
                "AI PRODUCT DEVELOPMENT",
                "AI",
                [
                    "artificial intelligence",
                    "generative ai",
                    "machine learning",
                    "large language model",
                    "foundation model",
                ],
            ),

            (
                "NEW PRODUCT ACTIVITY",
                "PRODUCT",
                [
                    "launched",
                    "introduced",
                    "released",
                    "commercial launch",
                    "new product",
                    "new service",
                ],
            ),

            (
                "TECHNOLOGY DEVELOPMENT",
                "TECHNOLOGY",
                [
                    "technology platform",
                    "proprietary technology",
                    "innovation",
                    "patent",
                    "intellectual property",
                ],
            ),

            (
                "STRATEGIC PARTNERSHIP",
                "PARTNERSHIP",
                [
                    "strategic partnership",
                    "strategic alliance",
                    "collaboration",
                    "joint venture",
                    "partnered",
                ],
            ),

            (
                "MAJOR CONTRACT ACTIVITY",
                "CONTRACT",
                [
                    "contract award",
                    "customer agreement",
                    "multi-year agreement",
                    "government contract",
                ],
            ),

            (
                "BUSINESS EXPANSION",
                "EXPANSION",
                [
                    "new facility",
                    "new factory",
                    "capacity expansion",
                    "expanded operations",
                    "new market",
                ],
            ),

            (
                "ACQUISITION ACTIVITY",
                "ACQUISITION",
                [
                    "acquired",
                    "acquisition",
                    "business combination",
                    "merger",
                ],
            ),

            (
                "MANAGEMENT CHANGE",
                "MANAGEMENT",
                [
                    "appointed chief executive",
                    "appointed ceo",
                    "appointed cfo",
                    "leadership transition",
                    "management transition",
                ],
            ),
        ]


        for event_type, category, keywords in classifications:

            if any(
                keyword in sentence
                for keyword in keywords
            ):

                return {
                    "type": event_type,
                    "category": category,
                }


        return None


    def _validate_catalyst(self, sentence, event_type, filing):

        score = 0

        action_words = [
            "launched",
            "introduced",
            "released",
            "announced",
            "entered",
            "signed",
            "completed",
            "acquired",
            "appointed",
            "expanded",
            "developed",
            "implemented",
        ]


        if any(
            word in sentence
            for word in action_words
        ):
            score += 25


        if len(sentence) > 80:
            score += 20


        business_terms = [
            "customer",
            "revenue",
            "platform",
            "product",
            "commercial",
            "market",
            "production",
            "capacity",
            "deployment",
        ]


        if any(
            term in sentence
            for term in business_terms
        ):
            score += 25


        form = filing.get("form")


        if form == "8-K":
            score += 15

        elif form in [
            "10-Q",
            "10-K",
        ]:
            score += 10


        negative_terms = [
            "risk",
            "may",
            "could",
            "uncertainty",
            "subject to",
            "forward-looking",
            "potential",
            "cannot",
        ]


        if any(
            term in sentence
            for term in negative_terms
        ):
            score -= 30


        return max(
            0,
            min(
                score,
                100
            )
        )
        
    def _scan_filing_text(self, filing_text, filing):

        events = []

        counts = {
            "new_products": 0,
            "ai_mentions": 0,
            "technology_mentions": 0,
            "partnerships": 0,
            "contracts": 0,
            "expansions": 0,
            "acquisitions": 0,
            "management_changes": 0,
        }


        sentences = self._extract_candidate_sentences(
            filing_text
        )


        for sentence in sentences:

            classification = self._classify_event(
                sentence
            )

            if not classification:
                continue


            confidence = self._validate_catalyst(
                sentence,
                classification["type"],
                filing
            )


            if confidence < 70:
                continue


            category = classification["category"]


            if category == "AI":
                counts["ai_mentions"] += 1

            elif category == "PRODUCT":
                counts["new_products"] += 1

            elif category == "TECHNOLOGY":
                counts["technology_mentions"] += 1

            elif category == "PARTNERSHIP":
                counts["partnerships"] += 1

            elif category == "CONTRACT":
                counts["contracts"] += 1

            elif category == "EXPANSION":
                counts["expansions"] += 1

            elif category == "ACQUISITION":
                counts["acquisitions"] += 1

            elif category == "MANAGEMENT":
                counts["management_changes"] += 1


            if confidence >= 85:
                materiality = "HIGH"

            elif confidence >= 75:
                materiality = "MEDIUM"

            else:
                materiality = "LOW"


            events.append({

                "type":
                    classification["type"],

                "category":
                    classification["category"],

                "confidence":
                    confidence,

                "catalyst":
                    True,

                "materiality":
                    materiality,

                "filing":
                    filing.get("form"),

                "date":
                    filing.get("filing_date"),

                "accession_number":
                    filing.get("accession_number"),

                "document":
                    filing.get("document"),

                "evidence":
                    sentence,

            })


        return events, counts

    def _score_n_component(self, report):

        score = 0

        events = report.get(
            "events",
            []
        )


        high_events = sum(
            1
            for event in events
            if event.get("materiality") == "HIGH"
        )


        medium_events = sum(
            1
            for event in events
            if event.get("materiality") == "MEDIUM"
        )


        score += high_events * 25
        score += medium_events * 10


        innovation = (
            report.get("new_products",0)
            +
            report.get("ai_mentions",0)
            +
            report.get("technology_mentions",0)
        )


        if innovation >= 5:
            innovation_state = "ELITE"

        elif innovation >= 3:
            innovation_state = "STRONG"

        elif innovation >= 1:
            innovation_state = "MODERATE"

        else:
            innovation_state = "LOW"


        catalyst_score = len(events)


        if catalyst_score >= 5:
            momentum = "VERY HIGH"

        elif catalyst_score >= 3:
            momentum = "HIGH"

        elif catalyst_score >= 1:
            momentum = "MODERATE"

        else:
            momentum = "LOW"


        final_score = min(
            score,
            100
        )


        return {

            "catalyst_score":
                catalyst_score,

            "strategic_momentum":
                momentum,

            "innovation_state":
                innovation_state,

            "score":
                final_score,

            "quality":
                self._quality(
                    final_score
                ),
        }

    def _quality(self,score):
        if score>=85:
            return "VERY STRONG"
        if score>=70:
            return "STRONG"
        if score>=55:
            return "POSITIVE"
        if score>=40:
            return "MODERATE"
        return "WEAK"

    def _log_report(self,report):
        logger.info("-"*70)
        for filing in report.get("filings_reviewed",[]):
            logger.info(
                "%s  %s  %s",
                filing.get("form"),
                filing.get("date"),
                filing.get("document"),
            )

        logger.info("-"*70)
        logger.info("DISCOVERED DEVELOPMENTS:")
        logger.info("-"*70)
        for event in report.get("events",[]):

            if event.get("confidence",0) < 50:
                continue
            logger.info("")
            logger.info("%s",event.get("type"))
            logger.info("Date: %s",event.get("date"))
            logger.info("Source: %s",event.get("filing"))
            logger.info("Document: %s",event.get("document"))
            logger.info("Accession: %s",event.get("accession_number"))
            logger.info("Confidence: %s",event.get("confidence"))            
            logger.info("%s",event.get("evidence"))

        logger.info("CANSLIM N ASSESSMENT:")
        logger.info("-"*70)
        logger.info("Innovation State       : %s",report.get("innovation_state"))
        logger.info("Strategic Momentum     : %s",report.get("strategic_momentum"))
        logger.info("Catalyst Score         : %s",report.get("catalyst_score"))
        logger.info("Score                  : %s",report.get("score"))
        logger.info("Quality                : %s",report.get("quality"))
        logger.info("="*70)

    def _empty_report(self):
        return {
            "ticker": None,
            "filings_reviewed": [],
            "events": [],
            "new_products": 0,
            "ai_mentions": 0,
            "technology_mentions": 0,
            "partnerships": 0,
            "contracts": 0,
            "expansions": 0,
            "acquisitions": 0,
            "management_changes": 0,
            "innovation_state": "UNKNOWN",
            "strategic_momentum": "UNKNOWN",
            "catalyst_score": 0,
            "score": 0,
            "quality": "NO DATA",
        }
"""
====================================================================
NEA28 SEC CONCEPT RESOLVER

Module:
    sec_concept_resolver.py

Purpose:
    Universal resolver for the NEA28 SEC XBRL concept registry.

Features:
    - Registry key resolver
    - Keyword discovery resolver
    - Concept search
    - Registry discovery
    - Reverse lookup
    - Plugin independent

Used By:
    All SEC Analysis Plugins
====================================================================
"""

from modules.stock_data_db.sec_financials_db.sec_concepts import (
    SEC_REGISTRIES,
)

import sqlite3

from modules.path_resolver import get_sec_financial_db_path

LIBRARY_DB = get_sec_financial_db_path()


def library_keyword_search(
    keywords
):

    if isinstance(keywords,str):

        keywords = (
            keywords
            .replace("_"," ")
            .replace("-"," ")
            .lower()
            .split()
        )


    conn = sqlite3.connect(
        LIBRARY_DB
    )

    cursor = conn.cursor()


    cursor.execute(
        """
        SELECT concept
        FROM concepts
        """
    )


    rows = cursor.fetchall()

    conn.close()


    matches=[]


    for row in rows:

        concept = row[0].lower()

        if all(
            word in concept
            for word in keywords
        ):
            matches.append(
                normalize(concept)
            )


    return _unique(matches)
    
# ============================================================
# Keyword Discovery Resolver
# ============================================================

def resolve_by_keywords(
    keywords,
    normalize_names=True
):
    """
    Dynamically discovers concepts from SEC registry keys.
    """

    if isinstance(keywords, str):
        keywords = (
            keywords
            .replace("_"," ")
            .replace("-"," ")
            .split()
        )

    matches = []

    for registry in SEC_REGISTRIES.values():

        for key, value in registry.items():

            key_text = normalize_key(key)

            if all(
                word.lower()
                in key_text
                for word in keywords
            ):

                if isinstance(value, str):

                    matches.append(
                        normalize(value)
                        if normalize_names
                        else value
                    )

                elif isinstance(value, (list, tuple, set)):

                    matches.extend(
                        normalize_list(value)
                        if normalize_names
                        else value
                    )

    library_matches = library_keyword_search(
        keywords
    )

    matches.extend(
        library_matches
    )

    return _unique(matches)
    
def search_concepts(
    text,
    normalize_names=True
):

    results = []

    text = text.lower()

    for registry_name, registry in SEC_REGISTRIES.items():

        for key, value in registry.items():

            if text in normalize_key(key):

                if isinstance(value, str):
                    concepts = [
                        normalize(value)
                        if normalize_names
                        else value
                    ]

                else:
                    concepts = (
                        normalize_list(value)
                        if normalize_names
                        else list(value)
                    )

                results.append(
                    {
                        "registry": registry_name,
                        "key": key,
                        "concepts": concepts
                    }
                )

    return results    

# ============================================================
# Normalization
# ============================================================

def normalize(concept):

    if concept is None:
        return None

    concept = str(concept)

    if ":" in concept:
        concept = concept.split(":")[-1]

    return concept.strip()


def normalize_list(concepts):
    return [
        normalize(c)
        for c in concepts
        if c
    ]
    
def normalize_key(value):

    return (
        str(value)
        .replace("_", " ")
        .lower()
        .strip()
    )       

def _unique(values):

    seen = set()
    result = []

    for value in values:

        if value not in seen:
            result.append(value)
            seen.add(value)

    return result
    
# ============================================================
# Registry Key Resolver
# ============================================================

def resolve(key, normalize_names=True):

    if not key:
        return [] if normalize_names else None

    key_upper = key.upper()

    # Registry key lookup
    for registry in SEC_REGISTRIES.values():

        if key_upper in registry:

            value = registry[key_upper]

            if isinstance(value,str):
                return (
                    normalize(value)
                    if normalize_names
                    else value
                )

            return (
                normalize_list(value)
                if normalize_names
                else list(value)
            )

    return [] if normalize_names else None


def resolve_key(key, normalize_names=True):
    return resolve(key, normalize_names)


def resolve_concept(key, normalize_names=True):
    return resolve(key, normalize_names)
    
# ============================================================
# Universal Concept Resolver
# ============================================================

def resolve_concepts(
    requests,
    normalize_names=True
):

    if isinstance(requests, str):
        requests = [requests]


    concepts = []


    for request in requests:

        exact = resolve(
            request,
            normalize_names
        )

        if exact:

            if isinstance(exact,list):
                concepts.extend(exact)

            else:
                concepts.append(exact)

            continue


        discovered = resolve_by_keywords(
            request,
            normalize_names
        )

        concepts.extend(
            discovered
        )


    return _unique(concepts)

def resolve_xbrl_concept(concept):

    concept = normalize(concept)

    for registry in SEC_REGISTRIES.values():

        for key,value in registry.items():

            values = (
                [value]
                if isinstance(value,str)
                else value
            )

            for item in values:

                if normalize(item) == concept:
                    return key

    return None
    
# ============================================================
# Registry Access
# ============================================================

def registry(name):
    return SEC_REGISTRIES.get(
        name.upper(),
        {}
    )


def registry_names():
    return list(SEC_REGISTRIES.keys())


def all_concepts(normalize_names=True):

    concepts = []

    for registry in SEC_REGISTRIES.values():

        for value in registry.values():

            if isinstance(value, str):

                concepts.append(
                    normalize(value)
                    if normalize_names
                    else value
                )

            elif isinstance(value, (list, tuple, set)):

                concepts.extend(
                    normalize_list(value)
                    if normalize_names
                    else value
                )


    return _unique(concepts)

# ============================================================
# Reverse Lookup
# ============================================================

def concept_map(normalize_names=True):

    mapping = {}

    for registry_name, registry in SEC_REGISTRIES.items():

        for key, value in registry.items():

            if isinstance(value, str):

                mapping[key] = {
                    "registry": registry_name,
                    "concepts": [
                        normalize(value)
                        if normalize_names
                        else value
                    ],
                }

            else:

                mapping[key] = {
                    "registry": registry_name,
                    "concepts": (
                        normalize_list(value)
                        if normalize_names
                        else list(value)
                    ),
                }

    return mapping


def find_registry(key):
    key = key.upper()
    for registry_name, registry in SEC_REGISTRIES.items():
        if key in registry:
            return registry_name
    return None

def exists(key):
    return find_registry(key) is not None
    
def registry_count():

    return {
        name: len(values)
        for name, values in SEC_REGISTRIES.items()
    }
    
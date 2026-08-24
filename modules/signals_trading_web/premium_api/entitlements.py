"""
NEA28V1 Premium API
Customer Entitlements
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import requests

from .config import config


class EntitlementError(Exception):
    """Raised when Shopify entitlement lookup fails."""


@dataclass(frozen=True)
class Entitlement:
    customer_id: str
    active: bool
    tier: str | None
    tags: tuple[str, ...]


TIER_TAGS = {
    "NEA_PREMIUM_STARTER": "starter",
    "NEA_PREMIUM_TRADER": "trader",
    "NEA_PREMIUM_PRO": "pro",
    "NEA_PREMIUM_ELITE": "elite",
}


TIER_RANK = {
    "none": 0,
    "starter": 1,
    "trader": 2,
    "pro": 3,
    "elite": 4,
}


CUSTOMER_QUERY = """
query GetCustomer($id: ID!) {
    customer(id: $id) {
        id
        tags
    }
}
"""


def _customer_gid(
    customer_id: str,
) -> str:
    return (
        "gid://shopify/Customer/"
        f"{customer_id}"
    )


def _shopify_graphql(
    query: str,
    variables: dict[str, Any],
) -> dict[str, Any]:

    response = requests.post(
        config.shopify_graphql_url,
        headers={
            "Content-Type": "application/json",
            "X-Shopify-Access-Token":
                config.SHOPIFY_ADMIN_ACCESS_TOKEN,
        },
        json={
            "query": query,
            "variables": variables,
        },
        timeout=10,
    )

    response.raise_for_status()

    payload = response.json()

    if payload.get("errors"):
        raise EntitlementError(
            "Shopify GraphQL returned an error."
        )

    return payload


def _resolve_tier(
    tags: list[str],
) -> str | None:

    normalized = {
        tag.strip().upper()
        for tag in tags
    }

    matching_tiers = [
        tier
        for tag, tier in TIER_TAGS.items()
        if tag in normalized
    ]

    if not matching_tiers:
        return None

    return max(
        matching_tiers,
        key=lambda tier: TIER_RANK[tier],
    )


def get_customer_entitlement(
    customer_id: str,
) -> Entitlement:

    if not customer_id.isdigit():
        raise EntitlementError(
            "Invalid customer ID."
        )

    payload = _shopify_graphql(
        CUSTOMER_QUERY,
        {
            "id": _customer_gid(customer_id),
        },
    )

    customer = (
        payload
        .get("data", {})
        .get("customer")
    )

    if not customer:
        return Entitlement(
            customer_id=customer_id,
            active=False,
            tier=None,
            tags=(),
        )

    tags = customer.get("tags") or []

    tier = _resolve_tier(tags)

    return Entitlement(
        customer_id=customer_id,
        active=tier is not None,
        tier=tier,
        tags=tuple(tags),
    )


def require_tier(
    entitlement: Entitlement,
    minimum_tier: str,
) -> None:

    if minimum_tier not in TIER_RANK:
        raise ValueError(
            f"Unknown NEA tier: {minimum_tier}"
        )

    if not entitlement.active:
        raise PermissionError(
            "No active NEA Premium entitlement."
        )

    actual_rank = TIER_RANK.get(
        entitlement.tier or "none",
        0,
    )

    required_rank = TIER_RANK[
        minimum_tier
    ]

    if actual_rank < required_rank:
        raise PermissionError(
            "Premium tier does not permit "
            "this resource."
        )
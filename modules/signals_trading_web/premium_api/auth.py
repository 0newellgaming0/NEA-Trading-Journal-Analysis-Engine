"""
NEA28V1 Premium API
Shopify App Proxy Authentication
"""

from __future__ import annotations

import hashlib
import hmac
import time
from dataclasses import dataclass
from typing import Mapping
from urllib.parse import parse_qsl

from flask import Request

from .config import config


class AuthenticationError(Exception):
    """Raised when a Shopify request cannot be authenticated."""


@dataclass(frozen=True)
class ShopifyIdentity:
    shop: str
    customer_id: str | None
    timestamp: int


def _build_shopify_message(
    query_string: bytes,
) -> tuple[str, str | None]:
    """
    Build Shopify's App Proxy signature message.

    Shopify's signature is calculated from all query parameters
    except 'signature', sorted by key, concatenated as:

        key=value&key=value

    Returns:
        canonical_message
        provided_signature
    """

    raw_query = query_string.decode(
        "utf-8",
        errors="strict",
    )

    parameters = parse_qsl(
        raw_query,
        keep_blank_values=True,
        strict_parsing=False,
    )

    signature = None
    filtered: list[tuple[str, str]] = []

    for key, value in parameters:
        if key == "signature":
            signature = value
        else:
            filtered.append((key, value))

    filtered.sort(
        key=lambda item: (item[0], item[1])
    )

    message = "&".join(
        f"{key}={value}"
        for key, value in filtered
    )

    return message, signature


def verify_shopify_signature(
    request: Request,
) -> bool:
    """
    Verify the Shopify App Proxy HMAC signature.
    """

    message, provided_signature = (
        _build_shopify_message(
            request.query_string
        )
    )

    if not provided_signature:
        return False

    expected_signature = hmac.new(
        config.SHOPIFY_APP_SECRET.encode("utf-8"),
        message.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(
        expected_signature,
        provided_signature,
    )


def _validate_timestamp(
    request: Request,
) -> int:
    timestamp_raw = request.args.get("timestamp")

    if not timestamp_raw:
        raise AuthenticationError(
            "Missing Shopify request timestamp."
        )

    try:
        timestamp = int(timestamp_raw)
    except ValueError as exc:
        raise AuthenticationError(
            "Invalid Shopify request timestamp."
        ) from exc

    now = int(time.time())

    if abs(now - timestamp) > config.SHOPIFY_SIGNATURE_MAX_AGE:
        raise AuthenticationError(
            "Expired Shopify request."
        )

    return timestamp


def _validate_shop(
    request: Request,
) -> str:
    shop = request.args.get("shop", "").strip().lower()

    if not shop:
        raise AuthenticationError(
            "Missing Shopify shop."
        )

    if shop != config.SHOPIFY_SHOP_DOMAIN:
        raise AuthenticationError(
            "Unauthorized Shopify shop."
        )

    return shop


def _customer_id(
    request: Request,
) -> str | None:
    """
    Return the Shopify customer ID supplied by the verified
    App Proxy request.

    Shopify supplies this only when a customer is logged in.
    """

    value = request.args.get(
        "logged_in_customer_id"
    )

    if not value:
        return None

    value = value.strip()

    if not value.isdigit():
        raise AuthenticationError(
            "Invalid Shopify customer ID."
        )

    return value


def authenticate_shopify_request(
    request: Request,
    require_customer: bool = False,
) -> ShopifyIdentity:
    """
    Authenticate an incoming Shopify App Proxy request.

    Authentication sequence:

        1. Verify HMAC.
        2. Validate shop.
        3. Validate timestamp.
        4. Extract logged-in customer ID.
        5. Optionally require a logged-in customer.
    """

    if not verify_shopify_signature(request):
        raise AuthenticationError(
            "Invalid Shopify signature."
        )

    shop = _validate_shop(request)

    timestamp = _validate_timestamp(request)

    customer_id = _customer_id(request)

    if require_customer and not customer_id:
        raise AuthenticationError(
            "A logged-in Shopify customer is required."
        )

    return ShopifyIdentity(
        shop=shop,
        customer_id=customer_id,
        timestamp=timestamp,
    )
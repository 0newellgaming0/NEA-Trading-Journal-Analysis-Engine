"""
NEA28V1 Premium API
HTTP Routes
"""

from __future__ import annotations

from functools import wraps
from typing import Callable

from flask import (
    Blueprint,
    jsonify,
    request,
)

from .auth import (
    AuthenticationError,
    ShopifyIdentity,
    authenticate_shopify_request,
)

from .entitlements import (
    EntitlementError,
    get_customer_entitlement,
    require_tier,
)

from .premium_api import (
    DataNotFoundError,
    InvalidDataPathError,
    PremiumAPIError,
    PremiumDataAPI,
)


api = Blueprint(
    "nea_premium_api",
    __name__,
    url_prefix="/api",
)

data_api = PremiumDataAPI()


def _error(
    message: str,
    status: int,
):
    return jsonify(
        {
            "ok": False,
            "error": message,
        }
    ), status


def premium_required(
    minimum_tier: str = "starter",
):
    """
    Decorator for authenticated Premium endpoints.

    Authentication:
        Shopify App Proxy signature

    Authorization:
        Shopify customer entitlement
    """

    def decorator(
        function: Callable,
    ):

        @wraps(function)
        def wrapper(*args, **kwargs):

            try:
                identity = (
                    authenticate_shopify_request(
                        request,
                        require_customer=True,
                    )
                )

                assert identity.customer_id

                entitlement = (
                    get_customer_entitlement(
                        identity.customer_id
                    )
                )

                require_tier(
                    entitlement,
                    minimum_tier,
                )

                return function(
                    identity,
                    entitlement,
                    *args,
                    **kwargs,
                )

            except AuthenticationError as exc:
                return _error(
                    str(exc),
                    401,
                )

            except EntitlementError as exc:
                return _error(
                    str(exc),
                    502,
                )

            except PermissionError as exc:
                return _error(
                    str(exc),
                    403,
                )

        return wrapper

    return decorator


@api.get("/health")
def health():
    return jsonify(
        {
            "ok": True,
            "service": "NEA28V1 Premium API",
            "status": "operational",
        }
    )


@api.get("/public/top10")
def public_top10():

    try:
        return jsonify(
            {
                "ok": True,
                "data": data_api.top10(),
            }
        )

    except PremiumAPIError as exc:
        return _error(
            str(exc),
            404,
        )


@api.get("/public/market-bias")
def public_market_bias():

    try:
        return jsonify(
            {
                "ok": True,
                "data": data_api.market_bias(),
            }
        )

    except PremiumAPIError as exc:
        return _error(
            str(exc),
            404,
        )


@api.get("/public/newsletter")
def public_newsletter():

    try:
        return jsonify(
            {
                "ok": True,
                "data": data_api.newsletter(),
            }
        )

    except PremiumAPIError as exc:
        return _error(
            str(exc),
            404,
        )


@api.get("/premium/me")
@premium_required("starter")
def premium_identity(
    identity: ShopifyIdentity,
    entitlement,
):

    return jsonify(
        {
            "ok": True,
            "customer_id":
                entitlement.customer_id,
            "tier":
                entitlement.tier,
            "active":
                entitlement.active,
        }
    )


@api.get("/premium/trades")
@premium_required("starter")
def premium_trades(
    identity: ShopifyIdentity,
    entitlement,
):

    try:
        return jsonify(
            {
                "ok": True,
                "tier":
                    entitlement.tier,
                "data":
                    data_api.trades(),
            }
        )

    except PremiumAPIError as exc:
        return _error(
            str(exc),
            404,
        )


@api.get("/premium/rankings")
@premium_required("trader")
def premium_rankings(
    identity: ShopifyIdentity,
    entitlement,
):

    try:
        return jsonify(
            {
                "ok": True,
                "tier":
                    entitlement.tier,
                "data":
                    data_api.rankings(),
            }
        )

    except PremiumAPIError as exc:
        return _error(
            str(exc),
            404,
        )


@api.get("/premium/risk")
@premium_required("pro")
def premium_risk(
    identity: ShopifyIdentity,
    entitlement,
):

    try:
        return jsonify(
            {
                "ok": True,
                "tier":
                    entitlement.tier,
                "data":
                    data_api.risk(),
            }
        )

    except PremiumAPIError as exc:
        return _error(
            str(exc),
            404,
        )


@api.get("/premium/analysis")
@premium_required("elite")
def premium_analysis(
    identity: ShopifyIdentity,
    entitlement,
):

    try:
        return jsonify(
            {
                "ok": True,
                "tier":
                    entitlement.tier,
                "data":
                    data_api.analysis(),
            }
        )

    except PremiumAPIError as exc:
        return _error(
            str(exc),
            404,
        )


@api.errorhandler(404)
def not_found(_error):
    return _error(
        "NEA API endpoint not found.",
        404,
    )
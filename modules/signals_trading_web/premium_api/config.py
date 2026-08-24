"""
NEA28V1 Premium API
Configuration

All secrets are loaded from environment variables.
Never place Shopify secrets, API tokens, or signing secrets
directly in source code.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _required(name: str) -> str:
    value = os.getenv(name)

    if not value:
        raise RuntimeError(
            f"Required environment variable is missing: {name}"
        )

    return value.strip()


def _optional(name: str, default: str = "") -> str:
    value = os.getenv(name, default)
    return value.strip() if value else default


def _int(name: str, default: int) -> int:
    value = os.getenv(name)

    if value is None or value == "":
        return default

    try:
        return int(value)
    except ValueError as exc:
        raise RuntimeError(
            f"Environment variable {name} must be an integer."
        ) from exc


@dataclass(frozen=True)
class Config:
    SHOPIFY_SHOP_DOMAIN: str
    SHOPIFY_APP_SECRET: str
    SHOPIFY_ADMIN_ACCESS_TOKEN: str
    SHOPIFY_API_VERSION: str

    PUBLIC_DATA_DIR: Path
    PREMIUM_DATA_DIR: Path

    APP_PROXY_PREFIX: str

    SHOPIFY_SIGNATURE_MAX_AGE: int

    API_HOST: str
    API_PORT: int
    API_DEBUG: bool

    MAX_JSON_BYTES: int

    @property
    def shopify_graphql_url(self) -> str:
        return (
            f"https://{self.SHOPIFY_SHOP_DOMAIN}"
            f"/admin/api/{self.SHOPIFY_API_VERSION}/graphql.json"
        )


def load_config() -> Config:
    public_data_dir = Path(
        _optional(
            "NEA_PUBLIC_DATA_DIR",
            "data/public",
        )
    ).resolve()

    premium_data_dir = Path(
        _optional(
            "NEA_PREMIUM_DATA_DIR",
            "data/premium",
        )
    ).resolve()

    return Config(
        SHOPIFY_SHOP_DOMAIN=_required(
            "SHOPIFY_SHOP_DOMAIN"
        ).lower(),

        SHOPIFY_APP_SECRET=_required(
            "SHOPIFY_APP_SECRET"
        ),

        SHOPIFY_ADMIN_ACCESS_TOKEN=_required(
            "SHOPIFY_ADMIN_ACCESS_TOKEN"
        ),

        SHOPIFY_API_VERSION=_optional(
            "SHOPIFY_API_VERSION",
            "2026-07",
        ),

        PUBLIC_DATA_DIR=public_data_dir,
        PREMIUM_DATA_DIR=premium_data_dir,

        APP_PROXY_PREFIX=_optional(
            "NEA_APP_PROXY_PREFIX",
            "/apps/nea28v1",
        ),

        SHOPIFY_SIGNATURE_MAX_AGE=_int(
            "SHOPIFY_SIGNATURE_MAX_AGE",
            300,
        ),

        API_HOST=_optional(
            "NEA_API_HOST",
            "127.0.0.1",
        ),

        API_PORT=_int(
            "NEA_API_PORT",
            8000,
        ),

        API_DEBUG=_optional(
            "NEA_API_DEBUG",
            "false",
        ).lower() in {
            "1",
            "true",
            "yes",
        },

        MAX_JSON_BYTES=_int(
            "NEA_MAX_JSON_BYTES",
            5 * 1024 * 1024,
        ),
    )


config = load_config()
# 📘 webull_exceptions.py — README

## Purpose
Defines all custom error handling classes for the Webull system.

Ensures consistent error reporting across:
- Downloader
- Client
- Streaming engine

## Exception Types
- WebullError: Base class
- AuthError: Login failure
- TokenExpiredError: Session expired
- MarketDataError: Data fetch failure
- SymbolError: Invalid ticker
- DataValidationError: Bad OHLCV structure

## Usage Example
raise DataValidationError("Missing OHLC column")

## Why It Matters
Ensures:
- structured pipelines
- deterministic failures
- safe fallback behavior

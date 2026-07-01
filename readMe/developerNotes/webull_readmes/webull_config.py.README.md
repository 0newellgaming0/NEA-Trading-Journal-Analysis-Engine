# 📘 webull_config.py — README

## Purpose
This module defines all global configuration values used across the Webull integration system.

It acts as the single source of truth for:
- API credentials
- File paths
- Timeframe mappings
- Request limits
- Data formatting rules

## Key Responsibilities

### API Credentials
Stores:
- APP_KEY
- APP_SECRET

Used by webull_client.py for SDK authentication.

### Cache Paths
- Token storage
- Session persistence
- Cache directory structure

### Market Data Settings
Supported timeframes:
- 1m, 5m, 15m, 30m, 60m, daily, weekly, monthly

## How It Is Used
from .webull_config import APP_KEY, APP_SECRET

## Notes
- DO NOT hardcode credentials elsewhere
- Keep environment-controlled in production

# 📘 webull_symbols.py — README

## Purpose
Standardizes ticker formatting across the system.

## Functions
- normalize_symbol(" aapl ") -> "AAPL"
- validate_symbol(symbol)

## Usage
symbol = normalize_symbol(symbol)

## Why Important
Prevents:
- invalid API calls
- cache mismatches
- duplicate tickers

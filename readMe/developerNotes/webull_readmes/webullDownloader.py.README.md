# 📘 webullDownloader.py — README

## Purpose
NEA28 drop-in replacement for Yahoo downloader.

## Core Functions
- download_stock_data("AAPL", "daily", years=5)
- update_stock_data("AAPL", "daily")
- download_watchlist(["AAPL","TSLA"])

## Pipeline Flow
WebullClient → Raw DataFrame → Normalization → Validation → Filter → Return

## Output Format
Date | Open | High | Low | Close | Adj Close | Volume

## Critical Rule
NO downstream engine changes required

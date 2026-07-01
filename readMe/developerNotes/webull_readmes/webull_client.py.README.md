# 📘 webull_client.py — README

## Purpose
Core SDK wrapper layer.

ONLY module interacting with Webull OpenAPI SDK.

## Responsibilities
- Market data (OHLCV)
- Intraday candles
- Quotes
- Fundamentals
- News

## Example
client = WebullClient()
client.connect()

df = client.get_historical("AAPL", "daily")

## Output Format
date | open | high | low | close | volume

## Rule
Do NOT normalize here.
Normalization happens in webullDownloader.py

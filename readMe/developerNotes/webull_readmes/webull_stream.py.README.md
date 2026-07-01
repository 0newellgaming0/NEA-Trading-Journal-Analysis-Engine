# 📘 webull_stream.py — README

## Purpose
Real-time streaming engine for live market data.

## Features
- Live quote subscription
- Continuous polling loop
- Event queue system
- Engine feed output

## Workflow
Subscribe → Stream → Fetch → Queue → Emit

## Output Example
{
  "symbol": "AAPL",
  "price": 195.23,
  "volume": 1200000
}

## Future Upgrades
- WebSocket streaming
- MQTT feeds
- async event loop

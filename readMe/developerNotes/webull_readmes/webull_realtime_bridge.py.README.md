# 📘 webull_realtime_bridge.py — README

## Purpose
Connects streaming data into NEA28 trading engines.

## Connected Systems
- AO Engine
- AC Engine
- Alligator Engine
- Fractal Engine
- Candlestick Engine

## Flow
Webull Event → Bridge → Engines → Signals/Journal

## Design Rule
Pure integration layer (NO data logic)

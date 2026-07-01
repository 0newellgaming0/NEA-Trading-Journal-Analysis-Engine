# 📘 webull_event_bus.py — README

## Purpose
Central event routing system for NEA28 engines.

## Responsibilities
- Register handlers
- Emit events
- Decouple streaming from analysis

## Usage
bus.register("quote", handler)
bus.emit("quote", data)

## Event Types
- quote
- candle
- trade

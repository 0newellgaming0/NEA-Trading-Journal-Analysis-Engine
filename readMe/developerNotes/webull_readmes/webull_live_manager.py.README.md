# 📘 webull_live_manager.py — README

## Purpose
MASTER CONTROL SYSTEM for all real-time Webull operations.

## Responsibilities
- Initialize client
- Start stream engine
- Connect event bus
- Attach NEA engines
- Manage subscriptions

## Usage
manager.subscribe("AAPL")
manager.start()

## Architecture
Client → Stream → Event Bus → Bridge → Engines

## Importance
Entry point for live trading intelligence

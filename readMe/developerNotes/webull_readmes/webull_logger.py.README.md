# 📘 webull_logger.py — README

## Purpose
Central logging system for all Webull modules.

## Features
- Unified log format
- Timestamped output
- Module tagging (WEBULL)
- Debug/error tracking

## Usage
from .webull_logger import logger

logger.info("Downloading AAPL")

## Log Format
2026-07-01 12:00:00 | INFO | WEBULL | Downloading AAPL

## Best Practice
Use logging instead of print statements.

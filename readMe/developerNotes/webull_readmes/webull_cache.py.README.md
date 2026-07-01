# 📘 webull_cache.py — README

## Purpose
Handles persistent storage of session and authentication data.

## Stores
- Access tokens
- Session state
- Cached authentication results

## Files
- access_token.json
- session.json

## Functions
- save_token(token_data)
- load_token()
- save_session(session)

## Why It Matters
Prevents:
- repeated logins
- API throttling
- session expiration issues

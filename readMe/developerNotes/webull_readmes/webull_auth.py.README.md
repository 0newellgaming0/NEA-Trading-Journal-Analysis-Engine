# 📘 webull_auth.py — README

## Purpose
Handles authentication lifecycle for Webull OpenAPI.

## Responsibilities
- Login initialization
- Session restoration
- Token storage
- Logout handling

## Workflow
1. auth.login()
2. auth.restore()
3. auth.is_logged_in()

## SDK Integration
# self.client.login(APP_KEY, APP_SECRET)

## Important
Must remain isolated from:
- data logic
- analysis engines
- UI code

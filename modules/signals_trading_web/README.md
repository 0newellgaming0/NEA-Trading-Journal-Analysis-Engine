# Signals Trading Web

Public web layer for the automated Python/SQLite trading system.

## Architecture

The authoritative trade flow is:

```text
trades.db
   ↓
Python publication engine
   ↓
sanitized public JSON
   ↓
GitHub
   ↓
GitHub Pages
   ↓
Shopify
```

`trades.db` is the **single source of truth for generated trades**.

The publication system reads trades exclusively from `trades.db`. It does not use `signals.db`, `trading.db`, or `trade_tracker.db` to construct or reconstruct trades.

The public layer produces:

* `data/trades.json`
* `data/performance.json`
* `data/market.json`

Signals databases are not part of the publication pipeline.

The SQLite database remains authoritative and should not be committed to this repository.

## Local Setup

The publication engine resolves the authoritative database through the project's database path resolver.

No `SIGNALS_DB`, `TRADING_DB`, or `TRADE_TRACKER_DB` environment variables are required by the publication system.

Run the publisher:

```bash
python -m publisher.publish
```

Validate the generated public data:

```bash
python -m unittest discover -s tests -v
```

The publication process reads the authoritative `trades.db` and generates the public JSON files used by the dashboard.

## Public Trade Data

### `trades.json`

Contains sanitized trade records derived directly from `trades.db`.

Private fields such as broker trade IDs, account information, credentials, and other internal metadata are excluded by the public schema.

### `performance.json`

Contains aggregate performance information calculated from the authoritative trade records.

### `market.json`

Contains the public market-state payload used by the dashboard.

## Validation

The repository includes automated validation for:

* Python syntax
* publication modules
* public schema sanitization
* JSON structure
* performance data structure
* market data structure

Run the complete test suite locally:

```bash
python -m unittest discover -s tests -v
```

GitHub Actions runs the same validation during pushes and pull requests.

## GitHub Pages

Enable GitHub Pages for the repository and select **GitHub Actions** as the deployment source.

The publication workflow:

1. Checks out the repository.
2. Sets up Python.
3. Publishes data from the authoritative `trades.db`.
4. Validates the generated JSON.
5. Validates the Python modules.
6. Runs the test suite.
7. Uploads the `dashboard/` directory.
8. Deploys the dashboard to GitHub Pages.

The dashboard consumes the public JSON layer rather than accessing SQLite directly.

## Shopify

Shopify is a downstream presentation/integration layer.

The simplest integration is a Shopify page containing an iframe pointing to the GitHub Pages dashboard.

Shopify does not become a source of truth and does not participate in trade generation or trade reconciliation.

## Data Authority

The system follows a strict authority model:

```text
Analysis / Signal Engines
        ↓
Trade Generation
        ↓
trades.db  ← AUTHORITATIVE
        ↓
Publication Engine
        ↓
Public JSON
        ↓
Dashboard
        ↓
GitHub Pages / Shopify
```

A signal does not become an official trade merely because it exists in an analysis database.

Only a trade recorded in `trades.db` is published as an authoritative generated trade.

## Security

Do not place the following in this repository:

* Broker credentials
* Webull identifiers
* Account numbers
* Account balances
* Private API keys
* Authentication tokens
* SQLite databases
* Private trading metadata
* Personally identifiable information
* Broker session information

Only sanitized, intentionally public trade information should be published.

## Repository Structure

```text
signals-trading-web/
│
├── .github/
│   └── workflows/
│       ├── publish.yml
│       └── validate.yml
│
├── dashboard/
│   ├── index.html
│   ├── trades.html
│   ├── signals.html
│   ├── performance.html
│   └── css/
│
├── data/
│   ├── trades.json
│   ├── performance.json
│   └── market.json
│
├── publisher/
│   ├── database_reader.py
│   ├── public_schema.py
│   ├── publication_engine.py
│   ├── validator.py
│   └── publish.py
│
├── scripts/
│
├── tests/
│
├── requirements.txt
└── README.md
```

> **Note:** If `dashboard/signals.html` still exists, it should not imply that the publication system obtains trade data from a signals database. Any signal display must use an explicitly separate public data source or be removed from the dashboard.

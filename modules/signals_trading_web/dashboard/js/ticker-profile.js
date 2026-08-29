"use strict";

document.addEventListener(
"DOMContentLoaded",
initializeTickerProfile
);

async function initializeTickerProfile() {

```
showLoading();

const ticker =
    getRequestedTicker();

if (!ticker) {

    showError(
        "No ticker was specified. Open a ticker profile from a published trade opportunity."
    );

    return;
}

try {

    const data =
        await loadTickerTradeData(
            ticker
        );

    const trades =
        normalizeTradeData(
            data
        );

    const trade =
        findTickerTrade(
            trades,
            ticker
        );

    if (!trade) {

        showError(
            `No published NEA28V1 trade data was found for ${ticker}.`
        );

        return;
    }

    renderTickerProfile(
        trade
    );

} catch (error) {

    console.error(
        "NEA28V1 ticker profile error:",
        error
    );

    showError(
        `Unable to load the published trade data for ${ticker}.`
    );
}
```

}

function getRequestedTicker() {

```
const params =
    new URLSearchParams(
        window.location.search
    );

const ticker =
    params.get("ticker");

if (!ticker) {
    return null;
}

const normalized =
    ticker
        .trim()
        .toUpperCase();

return normalized || null;
```

}

async function loadTickerTradeData(
ticker
) {

```
const url =
    `data/analysis/${encodeURIComponent(
        ticker
    )}/trades.json?t=${Date.now()}`;

const response =
    await fetch(
        url,
        {
            cache: "no-store"
        }
    );

if (!response.ok) {

    throw new Error(
        `Unable to load ${url}: ${response.status}`
    );
}

return await response.json();
```

}

function normalizeTradeData(data) {

```
let source = [];

if (Array.isArray(data)) {

    source = data;

} else if (
    data &&
    Array.isArray(data.trades)
) {

    source = data.trades;

} else if (
    data &&
    Array.isArray(data.data)
) {

    source = data.data;
}

return source
    .map(normalizeTrade)
    .filter(Boolean);
```

}

function normalizeTrade(trade) {

```
if (
    !trade ||
    typeof trade !== "object"
) {
    return null;
}

if (
    trade.ticker === null ||
    trade.ticker === undefined ||
    String(trade.ticker).trim() === ""
) {
    return null;
}

return {

    ticker:
        String(trade.ticker)
            .trim()
            .toUpperCase(),

    direction:
        displayValue(
            trade.direction
        ),

    setup:
        displayValue(
            trade.setup
        ),

    regime:
        displayValue(
            trade.regime
        ),

    timeframe:
        displayValue(
            trade.timeframe
        ),

    entry:
        numericValue(
            trade.entry
        ),

    stop:
        numericValue(
            trade.stop
        ),

    target:
        numericValue(
            trade.target
        ),

    riskReward:
        numericValue(
            trade.risk_reward
        ),

    score:
        numericValue(
            trade.score
        ),

    currentPrice:
        numericValue(
            trade.current_price
        ),

    status:
        displayValue(
            trade.status
        ),

    signalStrength:
        displayValue(
            trade.signal_strength
        ),

    confluence:
        displayValue(
            trade.confluence
        ),

    createdAt:
        trade.created_at,

    updatedAt:
        trade.updated_at
};
```

}

function findTickerTrade(
trades,
ticker
) {

```
return trades.find(
    trade =>
        trade.ticker === ticker
);
```

}

function renderTickerProfile(trade) {

```
setText(
    "ticker",
    trade.ticker
);

setText(
    "direction",
    trade.direction
);

setText(
    "setup",
    trade.setup
);

setText(
    "regime",
    trade.regime
);

setText(
    "timeframe",
    trade.timeframe
);

setText(
    "entry",
    formatPrice(
        trade.entry
    )
);

setText(
    "stop",
    formatPrice(
        trade.stop
    )
);

setText(
    "target",
    formatPrice(
        trade.target
    )
);

setText(
    "riskReward",
    formatRiskReward(
        trade.riskReward
    )
);

setText(
    "score",
    formatScore(
        trade.score
    )
);

setText(
    "currentPrice",
    formatPrice(
        trade.currentPrice
    )
);

setText(
    "status",
    trade.status
);

setText(
    "signalStrength",
    trade.signalStrength
);

setText(
    "confluence",
    formatConfluence(
        trade.confluence
    )
);

setText(
    "createdAt",
    formatTimestamp(
        trade.createdAt
    )
);

setText(
    "updatedAt",
    formatTimestamp(
        trade.updatedAt
    )
);

setText(
    "opportunityDescription",
    buildOpportunityDescription(
        trade
    )
);

document.title =
    `NEA28V1 ${trade.ticker} Ticker Profile`;

hideLoading();
hideError();
showProfile();
```

}

function buildOpportunityDescription(
trade
) {

```
const ticker =
    trade.ticker;

const direction =
    trade.direction;

const setup =
    trade.setup;

const regime =
    trade.regime;

const timeframe =
    trade.timeframe;

const score =
    formatScore(
        trade.score
    );

let description =
    `${ticker} is currently represented as a ` +
    `${direction} ${setup} opportunity within ` +
    `the published NEA28V1 ticker dataset.`;

if (regime !== "—") {

    description +=
        ` The current market regime is ${regime}.`;
}

if (timeframe !== "—") {

    description +=
        ` The published signal timeframe is ${timeframe}.`;
}

if (score !== "—") {

    description +=
        ` The published NEA28V1 ranking score is ${score}.`;
}

description +=
    " Market conditions, liquidity, news, execution conditions, " +
    "and the underlying trade thesis should be independently " +
    "evaluated before making any trading decision.";

return description;
```

}

function numericValue(
value
) {

```
if (
    value === null ||
    value === undefined ||
    value === ""
) {
    return NaN;
}

if (
    typeof value === "number"
) {
    return Number.isFinite(value)
        ? value
        : NaN;
}

const number =
    Number(
        String(value)
            .replace(
                /[$,%]/g,
                ""
            )
            .trim()
    );

return Number.isFinite(number)
    ? number
    : NaN;
```

}

function displayValue(
value
) {

```
if (
    value === null ||
    value === undefined ||
    value === ""
) {
    return "—";
}

return String(value);
```

}

function formatPrice(
value
) {

```
if (!Number.isFinite(value)) {
    return "—";
}

return `$${value.toFixed(4)}`;
```

}

function formatRiskReward(
value
) {

```
if (!Number.isFinite(value)) {
    return "—";
}

return `${value.toFixed(2)}R`;
```

}

function formatScore(
value
) {

```
if (!Number.isFinite(value)) {
    return "—";
}

return Number.isInteger(value)
    ? String(value)
    : value.toFixed(2);
```

}

function formatConfluence(
value
) {

```
if (
    value === null ||
    value === undefined ||
    value === ""
) {
    return "—";
}

if (
    typeof value === "number" &&
    Number.isFinite(value)
) {
    return Number.isInteger(value)
        ? String(value)
        : value.toFixed(2);
}

return String(value);
```

}

function formatTimestamp(
value
) {

```
if (
    value === null ||
    value === undefined ||
    value === ""
) {
    return "—";
}

const date =
    new Date(value);

if (
    Number.isNaN(
        date.getTime()
    )
) {
    return String(value);
}

return date.toLocaleString(
    "en-US",
    {
        month: "short",
        day: "numeric",
        year: "numeric",
        hour: "numeric",
        minute: "2-digit"
    }
);
```

}

function setText(
id,
value
) {

```
const element =
    document.getElementById(
        id
    );

if (!element) {

    console.error(
        `NEA28V1 ticker profile: missing HTML element #${id}`
    );

    return;
}

element.textContent =
    value ?? "—";
```

}

function showLoading() {

```
const element =
    document.getElementById(
        "loadingState"
    );

if (element) {

    element.classList.remove(
        "hidden"
    );
}
```

}

function hideLoading() {

```
const element =
    document.getElementById(
        "loadingState"
    );

if (element) {

    element.classList.add(
        "hidden"
    );
}
```

}

function showProfile() {

```
const element =
    document.getElementById(
        "profileContent"
    );

if (element) {

    element.classList.remove(
        "hidden"
    );
}
```

}

function hideProfile() {

```
const element =
    document.getElementById(
        "profileContent"
    );

if (element) {

    element.classList.add(
        "hidden"
    );
}
```

}

function showError(
message
) {

```
hideLoading();
hideProfile();

const messageElement =
    document.getElementById(
        "errorMessage"
    );

if (messageElement) {

    messageElement.textContent =
        message;
}

const errorElement =
    document.getElementById(
        "errorState"
    );

if (errorElement) {

    errorElement.classList.remove(
        "hidden"
    );
}
```

}

function hideError() {

```
const element =
    document.getElementById(
        "errorState"
    );

if (element) {

    element.classList.add(
        "hidden"
    );
}
```

}

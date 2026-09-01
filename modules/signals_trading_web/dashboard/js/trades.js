"use strict";

/*

* ============================================================
* TRADES PAGE
* ============================================================
*
* PUBLIC DATA STRUCTURE
*
* data/
* analysis/
* 
  index.json
  
* 
  TICKER/
  
* 
    trades.json
  
*
* analysis/index.json:
*
* {
* 
  "tickers": {
  
* 
      "AAPL": [
  
* 
          "2026-08-29",
  
* 
          "2026-08-31",
  
* 
          "2026-09-01"
  
* 
      ],
  
* 
      ...
  
* 
  }
  
* }
*
* Each ticker's trades.json may contain multiple historical
* trade records.
*
* The selected date is matched against the ACTUAL trade date
* stored inside each trade record.
*
* ============================================================
  */

let allTrades = [];

let sortColumn = "score";
let sortDirection = "desc";

let selectedTrade = null;

let selectedDate = null;

let availableDates = [];

let dateSelectorInitialized = false;

/* ============================================================

* PATHS
* ============================================================ */

const ANALYSIS_DATA_PATH =
"data/analysis";

const ANALYSIS_INDEX_PATH =
"analysis/index.json";

/* ============================================================

* INITIALIZATION
* ============================================================ */

if (
document.readyState === "loading"
) {
document.addEventListener(
"DOMContentLoaded",
initializeTrades
);
} else {
initializeTrades();
}

/* ============================================================

* GENERIC JSON LOADER
* ============================================================ */

async function getJSON(file) {


const response =
    await fetch(
        "./data/" +
        file +
        "?t=" +
        Date.now(),
        {
            cache: "no-store"
        }
    );

if (!response.ok) {

    throw new Error(
        `${file}: HTTP ${response.status}`
    );
}

return response.json();


}

/* ============================================================

* URL PARAMETERS
* ============================================================ */

function getRequestedDate() {


const params =
    new URLSearchParams(
        window.location.search
    );

const requestedDate =
    params.get("date");

if (
    requestedDate &&
    isValidDateString(
        requestedDate
    )
) {
    return requestedDate;
}

return null;


}

function getRequestedTicker() {


const params =
    new URLSearchParams(
        window.location.search
    );

const ticker =
    params.get("ticker");

if (!ticker) {
    return null;
}

return ticker
    .trim()
    .toUpperCase();


}

/* ============================================================

* DATE HELPERS
* ============================================================ */

function getTodayDateKey() {


const now =
    new Date();

const year =
    now.getFullYear();

const month =
    String(
        now.getMonth() + 1
    ).padStart(
        2,
        "0"
    );

const day =
    String(
        now.getDate()
    ).padStart(
        2,
        "0"
    );

return (
    `${year}-${month}-${day}`
);


}

function isValidDateString(
value
) {


return (
    typeof value === "string" &&
    /^\d{4}-\d{2}-\d{2}$/.test(
        value
    )
);


}

function formatDateLabel(
date
) {


if (
    !isValidDateString(
        date
    )
) {
    return date;
}

const parts =
    date.split("-");

const year =
    Number(parts[0]);

const month =
    Number(parts[1]);

const day =
    Number(parts[2]);

const dateObject =
    new Date(
        year,
        month - 1,
        day
    );

return dateObject.toLocaleDateString(
    undefined,
    {
        year: "numeric",
        month: "long",
        day: "numeric"
    }
);


}

/* ============================================================

* TRADE DATE
* ============================================================
*
* IMPORTANT:
*
* The index date tells us which dates are available.
*
* The trade record itself determines the actual date of
* that trade.
*
* ============================================================ */

function getTradeDate(
trade
) {


if (
    !trade ||
    typeof trade !== "object"
) {
    return null;
}

const dateValue =
    trade.trade_date ??
    trade.tradeDate ??
    trade.date ??
    trade.created_at ??
    trade.createdAt ??
    trade.timestamp ??
    trade.generated_at ??
    trade.generatedAt ??
    trade.updated_at ??
    trade.updatedAt;

if (
    dateValue === null ||
    dateValue === undefined ||
    dateValue === ""
) {
    return null;
}

const text =
    String(
        dateValue
    ).trim();

/*
 * Direct YYYY-MM-DD.
 */
const directMatch =
    text.match(
        /^(\d{4}-\d{2}-\d{2})/
    );

if (directMatch) {

    return directMatch[1];
}

/*
 * ISO / JavaScript date.
 */
const parsed =
    new Date(
        dateValue
    );

if (
    Number.isNaN(
        parsed.getTime()
    )
) {
    return null;
}

return [
    parsed.getFullYear(),
    String(
        parsed.getMonth() + 1
    ).padStart(
        2,
        "0"
    ),
    String(
        parsed.getDate()
    ).padStart(
        2,
        "0"
    )
].join("-");


}

/* ============================================================

* TRADE TIMESTAMP
* ============================================================ */

function getTradeTimestamp(
trade
) {


if (
    !trade ||
    typeof trade !== "object"
) {
    return 0;
}

const timestamp =
    trade.trade_date ??
    trade.tradeDate ??
    trade.timestamp ??
    trade.created_at ??
    trade.createdAt ??
    trade.generated_at ??
    trade.generatedAt ??
    trade.updated_at ??
    trade.updatedAt;

if (
    timestamp === null ||
    timestamp === undefined ||
    timestamp === ""
) {
    return 0;
}

const parsed =
    new Date(
        timestamp
    ).getTime();

return Number.isFinite(
    parsed
)
    ? parsed
    : 0;


}

/* ============================================================

* GET AVAILABLE DATES
* ============================================================
*
* Uses the EXACT index structure used by index.js:
*
* index.tickers[TICKER] = [
* 
  "YYYY-MM-DD",
  
* 
  ...
  
* ]
*
* Dates are combined across all tickers.
* ============================================================ */

function getAvailableDates(
index
) {


const dateSet =
    new Set();

const tickers =
    index &&
    typeof index.tickers === "object" &&
    index.tickers !== null
        ? index.tickers
        : {};

Object.keys(
    tickers
).forEach(
    ticker => {

        const dates =
            Array.isArray(
                tickers[ticker]
            )
                ? tickers[ticker]
                : [];

        dates.forEach(
            date => {

                if (
                    isValidDateString(
                        date
                    )
                ) {
                    dateSet.add(
                        date
                    );
                }
            }
        );
    }
);

return [
    ...dateSet
].sort(
    (a, b) =>
        b.localeCompare(a)
);


}

/* ============================================================

* DATE SELECTOR
* ============================================================ */

function findDateSelector() {


/*
 * Prefer an existing selector if the HTML already has one.
 */
const existing =
    document.getElementById(
        "tradeDate"
    );

if (existing) {
    return existing;
}

/*
 * Create the selector inside the existing filter area.
 */
let container =
    document.getElementById(
        "tradeDateContainer"
    );

if (!container) {

    container =
        document.querySelector(
            ".filters"
        );
}

if (!container) {

    container =
        document.querySelector(
            ".controls"
        );
}

/*
 * If neither exists, use the table's parent.
 */
if (!container) {

    const table =
        document.querySelector(
            "table"
        );

    if (table) {

        container =
            table.parentElement;
    }
}

if (!container) {

    console.error(
        "Unable to create trade date selector: no controls container found."
    );

    return null;
}

const wrapper =
    document.createElement(
        "div"
    );

wrapper.id =
    "tradeDateContainer";

wrapper.className =
    "trade-date-control";

const label =
    document.createElement(
        "label"
    );

label.htmlFor =
    "tradeDate";

label.textContent =
    "Trade Date";

const selector =
    document.createElement(
        "select"
    );

selector.id =
    "tradeDate";

selector.name =
    "tradeDate";

selector.setAttribute(
    "aria-label",
    "Trade Date"
);

wrapper.appendChild(
    label
);

wrapper.appendChild(
    selector
);

container.prepend(
    wrapper
);

return selector;


}

function initializeDateSelector(
dates
) {


const selector =
    findDateSelector();

if (!selector) {
    return null;
}

selector.innerHTML = "";

if (!dates.length) {

    const option =
        document.createElement(
            "option"
        );

    option.value = "";

    option.textContent =
        "No trade dates available";

    selector.appendChild(
        option
    );

    selector.disabled =
        true;

    return selector;
}

selector.disabled =
    false;

const requestedDate =
    getRequestedDate();

/*
 * Requested date wins if it exists in the index.
 *
 * Otherwise use the newest published date.
 */
if (
    requestedDate &&
    dates.includes(
        requestedDate
    )
) {

    selectedDate =
        requestedDate;

} else {

    selectedDate =
        dates[0];
}

dates.forEach(
    date => {

        const option =
            document.createElement(
                "option"
            );

        option.value =
            date;

        option.textContent =
            formatDateLabel(
                date
            );

        if (
            date ===
            selectedDate
        ) {

            option.selected =
                true;
        }

        selector.appendChild(
            option
        );
    }
);

/*
 * Do not attach the change handler more than once.
 */
if (
    !dateSelectorInitialized
) {

    selector.addEventListener(
        "change",
        async () => {

            const date =
                selector.value;

            if (
                !isValidDateString(
                    date
                )
            ) {
                return;
            }

            selectedDate =
                date;

            updateUrlDate(
                date
            );

            const ticker =
                getRequestedTicker();

            await loadTradesForDate(
                date,
                ticker
            );
        }
    );

    dateSelectorInitialized =
        true;
}

updateUrlDate(
    selectedDate
);

return selector;


}

/* ============================================================

* UPDATE URL
* ============================================================ */

function updateUrlDate(
date
) {


if (
    !isValidDateString(
        date
    )
) {
    return;
}

const url =
    new URL(
        window.location.href
    );

url.searchParams.set(
    "date",
    date
);

window.history.replaceState(
    {},
    "",
    url
);


}

/* ============================================================

* LOAD ALL TRADES FOR DATE
* ============================================================
*
* This is the main correction.
*
* We do NOT require a ticker.
*
* We iterate through every ticker in index.json.
*
* For the selected date:
*
* 
  index.tickers[TICKER]
  
* 
           ↓
  
* 
  contains selected date?
  
* 
           ↓
  
* 
  load TICKER/trades.json
  
* 
           ↓
  
* 
  filter actual trade date
  
* 
           ↓
  
* 
  latest trade for that ticker
  
*
* ============================================================ */

async function loadTradesForDate(
date,
requestedTicker = null
) {


allTrades = [];

const index =
    window.__tradesIndex;

if (
    !index ||
    !index.tickers ||
    typeof index.tickers !== "object"
) {

    renderDataUnavailable(
        "Trade index unavailable."
    );

    return;
}

const tickers =
    index.tickers;

const tickerNames =
    Object.keys(
        tickers
    );

const loadedTrades = [];

/*
 * If a ticker is supplied in the URL, load only that
 * ticker. Otherwise this is the global Trades page.
 */
const tickersToLoad =
    requestedTicker
        ? tickerNames.filter(
            ticker =>
                ticker.toUpperCase() ===
                requestedTicker
        )
        : tickerNames;

for (
    const ticker of tickersToLoad
) {

    const dates =
        Array.isArray(
            tickers[ticker]
        )
            ? tickers[ticker]
            : [];

    /*
     * The index is the publication eligibility check.
     *
     * Never fall back to another date.
     */
    if (
        !dates.includes(
            date
        )
    ) {
        continue;
    }

    try {

        const data =
            await getJSON(
                `analysis/${encodeURIComponent(
                    ticker
                )}/trades.json`
            );

        const trades =
            Array.isArray(
                data.trades
            )
                ? data.trades
                : [];

        /*
         * Keep only records whose ACTUAL trade date
         * equals the selected date.
         */
        const matchingTrades =
            trades.filter(
                trade =>
                    getTradeDate(
                        trade
                    ) === date
            );

        if (
            !matchingTrades.length
        ) {
            continue;
        }

        /*
         * If multiple records exist for this ticker on
         * the selected date, use the latest one.
         */
        matchingTrades.sort(
            (a, b) =>
                getTradeTimestamp(b) -
                getTradeTimestamp(a)
        );

        const latestTrade =
            matchingTrades[0];

        loadedTrades.push({
            ...latestTrade,

            _ticker:
                ticker,

            _date:
                date
        });

    } catch (error) {

        console.error(
            `Failed to load trades for ${ticker} on ${date}:`,
            error
        );
    }
}

allTrades =
    loadedTrades;

renderTrades();


}

/* ============================================================

* INITIALIZATION
* ============================================================ */

async function initializeTrades() {


try {

    /*
     * Load the exact same index used by index.js.
     */
    const index =
        await getJSON(
            "analysis/index.json"
        );

    /*
     * Keep it available for date changes without
     * downloading index.json every time.
     */
    window.__tradesIndex =
        index;

    availableDates =
        getAvailableDates(
            index
        );

    /*
     * The selector is populated BEFORE loading trades.
     */
    const selector =
        initializeDateSelector(
            availableDates
        );

    if (
        !availableDates.length
    ) {

        renderDataUnavailable(
            "No published trade dates are available."
        );

        return;
    }

    /*
     * Use the actual selector value if available.
     */
    if (
        selector &&
        selector.value
    ) {

        selectedDate =
            selector.value;
    }

    /*
     * Load all tickers for the selected date.
     */
    await loadTradesForDate(
        selectedDate,
        getRequestedTicker()
    );

    initializeSorting();
    initializeFilters();
    initializeOrderDialog();

} catch (error) {

    console.error(
        "Failed to initialize trade data:",
        error
    );

    renderDataUnavailable(
        "Unable to load trade history."
    );
}


}

/* ============================================================

* RENDER TRADES
* ============================================================ */

function renderTrades() {


const body =
    document.getElementById(
        "trades"
    );

const noTrades =
    document.getElementById(
        "noTrades"
    );

const tradeCount =
    document.getElementById(
        "tradeCount"
    );

if (!body) {

    console.error(
        "Trades table body #trades was not found."
    );

    return;
}

const searchInput =
    document.getElementById(
        "tickerSearch"
    );

const directionFilter =
    document.getElementById(
        "directionFilter"
    );

const statusFilter =
    document.getElementById(
        "statusFilter"
    );

const search =
    searchInput
        ? searchInput.value
            .trim()
            .toUpperCase()
        : "";

const direction =
    directionFilter
        ? directionFilter.value
            .trim()
            .toUpperCase()
        : "";

const status =
    statusFilter
        ? statusFilter.value
            .trim()
            .toUpperCase()
        : "";

let trades =
    allTrades.filter(
        trade => {

            const ticker =
                String(
                    trade.ticker ||
                    trade._ticker ||
                    ""
                ).toUpperCase();

            const tradeDirection =
                String(
                    trade.direction ||
                    ""
                ).toUpperCase();

            const tradeStatus =
                String(
                    trade.status ||
                    ""
                ).toUpperCase();

            const matchesSearch =
                !search ||
                ticker.includes(
                    search
                );

            const matchesDirection =
                !direction ||
                tradeDirection ===
                    direction;

            const matchesStatus =
                !status ||
                tradeStatus ===
                    status;

            return (
                matchesSearch &&
                matchesDirection &&
                matchesStatus
            );
        }
    );

trades.sort(
    (a, b) => {

        const aValue =
            getSortValue(
                a,
                sortColumn
            );

        const bValue =
            getSortValue(
                b,
                sortColumn
            );

        let comparison = 0;

        if (
            typeof aValue ===
                "number" &&
            typeof bValue ===
                "number"
        ) {

            comparison =
                aValue - bValue;

        } else {

            comparison =
                String(
                    aValue
                ).localeCompare(
                    String(
                        bValue
                    ),
                    undefined,
                    {
                        numeric: true,
                        sensitivity:
                            "base"
                    }
                );
        }

        return (
            sortDirection === "asc"
                ? comparison
                : -comparison
        );
    }
);

body.innerHTML = "";

trades.forEach(
    trade => {

        const row =
            document.createElement(
                "tr"
            );

        row.className =
            "trade-row";

        const score =
            toNumber(
                trade.score
            );

        row.innerHTML = `
            <td>
                <b>
                    ${escapeHtml(
                        trade.ticker ||
                        trade._ticker ||
                        ""
                    )}
                </b>
            </td>

            <td>
                ${escapeHtml(
                    trade.direction ||
                    "—"
                )}
            </td>

            <td>
                ${escapeHtml(
                    trade.setup ||
                    "—"
                )}
            </td>

            <td>
                ${money(
                    trade.entry
                )}
            </td>

            <td>
                ${money(
                    trade.current_price
                )}
            </td>

            <td>
                ${money(
                    trade.stop
                )}
            </td>

            <td>
                ${money(
                    trade.target
                )}
            </td>

            <td>
                ${
                    score === null
                        ? "—"
                        : score.toFixed(
                            2
                        )
                }
            </td>

            <td>
                <span class="badge">
                    ${escapeHtml(
                        trade.status ||
                        "—"
                    )}
                </span>
            </td>
        `;

        row.addEventListener(
            "click",
            () => {

                const ticker =
                    String(
                        trade.ticker ||
                        trade._ticker ||
                        ""
                    )
                        .trim()
                        .toUpperCase();

                if (!ticker) {
                    return;
                }

                const date =
                    selectedDate;

                window.location.href =
                    `ticker-profile.html?ticker=${encodeURIComponent(
                        ticker
                    )}&date=${encodeURIComponent(
                        date
                    )}`;
            }
        );

        body.appendChild(
            row
        );
    }
);

if (tradeCount) {

    tradeCount.textContent =
        `${trades.length} of ` +
        `${allTrades.length} trades`;
}

if (noTrades) {

    noTrades.hidden =
        trades.length !== 0;
}

updateSortHeaders();

updateDisplayedDate();


}

/* ============================================================

* DISPLAY CURRENT DATE
* ============================================================ */

function updateDisplayedDate() {


const updated =
    document.getElementById(
        "updated"
    );

if (!updated || !selectedDate) {
    return;
}

updated.textContent =
    formatDateLabel(
        selectedDate
    );


}

/* ============================================================

* SORTING
* ============================================================ */

function getSortValue(
trade,
column
) {


const numericColumns = [
    "score",
    "entry",
    "current_price",
    "stop",
    "target"
];

if (
    numericColumns.includes(
        column
    )
) {

    const value =
        toNumber(
            trade[column]
        );

    return value === null
        ? -Infinity
        : value;
}

return String(
    trade[column] ?? ""
);


}

function updateSortHeaders() {


document
    .querySelectorAll(
        "th[data-sort]"
    )
    .forEach(
        th => {

            th.classList.remove(
                "sort-asc",
                "sort-desc"
            );

            if (
                th.dataset.sort ===
                sortColumn
            ) {

                th.classList.add(
                    sortDirection === "asc"
                        ? "sort-asc"
                        : "sort-desc"
                );
            }
        }
    );


}

function initializeSorting() {


document
    .querySelectorAll(
        "th[data-sort]"
    )
    .forEach(
        th => {

            th.addEventListener(
                "click",
                () => {

                    const column =
                        th.dataset.sort;

                    if (
                        sortColumn ===
                        column
                    ) {

                        sortDirection =
                            sortDirection ===
                            "asc"
                                ? "desc"
                                : "asc";

                    } else {

                        sortColumn =
                            column;

                        sortDirection =
                            column ===
                            "score"
                                ? "desc"
                                : "asc";
                    }

                    renderTrades();
                }
            );
        }
    );


}

/* ============================================================

* FILTERS
* ============================================================ */

function initializeFilters() {


const tickerSearch =
    document.getElementById(
        "tickerSearch"
    );

if (tickerSearch) {

    tickerSearch.addEventListener(
        "input",
        renderTrades
    );
}

const directionFilter =
    document.getElementById(
        "directionFilter"
    );

if (directionFilter) {

    directionFilter.addEventListener(
        "change",
        renderTrades
    );
}

const statusFilter =
    document.getElementById(
        "statusFilter"
    );

if (statusFilter) {

    statusFilter.addEventListener(
        "change",
        renderTrades
    );
}

const clearFilters =
    document.getElementById(
        "clearFilters"
    );

if (clearFilters) {

    clearFilters.addEventListener(
        "click",
        () => {

            if (tickerSearch) {
                tickerSearch.value = "";
            }

            if (directionFilter) {
                directionFilter.value = "";
            }

            if (statusFilter) {
                statusFilter.value = "";
            }

            renderTrades();
        }
    );
}


}

/* ============================================================

* ORDER DIALOG
* ============================================================ */

function openTradeOrder(
trade
) {


selectedTrade =
    trade;

const modal =
    document.getElementById(
        "orderModal"
    );

if (!modal) {
    return;
}

const ticker =
    String(
        trade.ticker ||
        trade._ticker ||
        ""
    ).toUpperCase();

const direction =
    String(
        trade.direction ||
        ""
    ).toUpperCase();

const side =
    direction === "BEARISH"
        ? "SELL"
        : "BUY";

document.getElementById(
    "orderTicker"
).value =
    ticker;

document.getElementById(
    "orderSide"
).value =
    side;

document.getElementById(
    "orderPrice"
).value =
    toNumber(
        trade.current_price
    ) ??
    toNumber(
        trade.entry
    ) ??
    "";

document.getElementById(
    "orderSubtitle"
).textContent =
    `${direction || "TRADE"} • ` +
    `${trade.setup || "Setup"}`;

document.getElementById(
    "summarySetup"
).textContent =
    trade.setup || "—";

document.getElementById(
    "summaryEntry"
).textContent =
    money(
        trade.entry
    );

document.getElementById(
    "summaryCurrent"
).textContent =
    money(
        trade.current_price
    );

document.getElementById(
    "summaryStop"
).textContent =
    money(
        trade.stop
    );

document.getElementById(
    "summaryTarget"
).textContent =
    money(
        trade.target
    );

const score =
    toNumber(
        trade.score
    );

document.getElementById(
    "summaryScore"
).textContent =
    score === null
        ? "—"
        : score.toFixed(
            2
        );

clearOrderMessage();

updateOrderTypeFields();

modal.classList.add(
    "visible"
);

modal.setAttribute(
    "aria-hidden",
    "false"
);

document.getElementById(
    "orderQuantity"
).focus();


}

function closeTradeOrder() {


const modal =
    document.getElementById(
        "orderModal"
    );

if (!modal) {
    return;
}

modal.classList.remove(
    "visible"
);

modal.setAttribute(
    "aria-hidden",
    "true"
);

selectedTrade =
    null;


}

function updateOrderTypeFields() {


const orderType =
    document.getElementById(
        "orderType"
    );

const field =
    document.getElementById(
        "limitPriceField"
    );

if (!orderType || !field) {
    return;
}

field.hidden =
    orderType.value !== "LIMIT";


}

function clearOrderMessage() {


const message =
    document.getElementById(
        "orderMessage"
    );

if (!message) {
    return;
}

message.textContent =
    "";

message.className =
    "order-message";


}

function showOrderMessage(
text,
type
) {


const message =
    document.getElementById(
        "orderMessage"
    );

if (!message) {
    return;
}

message.textContent =
    text;

message.className =
    "order-message visible " +
    type;


}

/* ============================================================

* SUBMIT ORDER
* ============================================================ */

async function submitTradeOrder() {


if (!selectedTrade) {

    showOrderMessage(
        "No trade selected.",
        "error"
    );

    return;
}

const ticker =
    document.getElementById(
        "orderTicker"
    ).value
        .trim()
        .toUpperCase();

const side =
    document.getElementById(
        "orderSide"
    ).value;

const orderType =
    document.getElementById(
        "orderType"
    ).value;

const quantity =
    Number(
        document.getElementById(
            "orderQuantity"
        ).value
    );

const limitPrice =
    Number(
        document.getElementById(
            "orderPrice"
        ).value
    );

if (!ticker) {

    showOrderMessage(
        "Ticker is required.",
        "error"
    );

    return;
}

if (
    !Number.isFinite(
        quantity
    ) ||
    quantity <= 0
) {

    showOrderMessage(
        "Enter a valid quantity.",
        "error"
    );

    return;
}

if (
    orderType === "LIMIT" &&
    (
        !Number.isFinite(
            limitPrice
        ) ||
        limitPrice <= 0
    )
) {

    showOrderMessage(
        "Enter a valid limit price.",
        "error"
    );

    return;
}

const submitButton =
    document.getElementById(
        "submitOrder"
    );

if (!submitButton) {
    return;
}

submitButton.disabled =
    true;

submitButton.textContent =
    "Submitting...";

clearOrderMessage();

try {

    const payload = {

        ticker:
            ticker,

        side:
            side,

        order_type:
            orderType,

        quantity:
            quantity,

        limit_price:
            orderType === "LIMIT"
                ? limitPrice
                : null,

        trade: {

            ticker:
                selectedTrade.ticker ||
                selectedTrade._ticker,

            direction:
                selectedTrade.direction,

            setup:
                selectedTrade.setup,

            entry:
                selectedTrade.entry,

            current_price:
                selectedTrade.current_price,

            stop:
                selectedTrade.stop,

            target:
                selectedTrade.target,

            score:
                selectedTrade.score,

            status:
                selectedTrade.status
        }
    };

    const response =
        await fetch(
            "/api/orders",
            {
                method: "POST",

                headers: {
                    "Content-Type":
                        "application/json"
                },

                body:
                    JSON.stringify(
                        payload
                    )
            }
        );

    let data = {};

    try {

        data =
            await response.json();

    } catch (error) {

        data = {};
    }

    if (!response.ok) {

        throw new Error(
            data.error ||
            data.message ||
            `Order HTTP ${response.status}`
        );
    }

    showOrderMessage(
        data.message ||
        "Webull order submitted successfully.",
        "success"
    );

    console.log(
        "Webull order response:",
        data
    );

    setTimeout(
        closeTradeOrder,
        1200
    );

} catch (error) {

    console.error(
        "Failed to submit Webull order:",
        error
    );

    showOrderMessage(
        error.message ||
        "Unable to submit order.",
        "error"
    );

} finally {

    submitButton.disabled =
        false;

    submitButton.textContent =
        "Place Webull Order";
}


}

/* ============================================================

* ORDER DIALOG INITIALIZATION
* ============================================================ */

function initializeOrderDialog() {


const closeButton =
    document.getElementById(
        "closeOrder"
    );

const cancelButton =
    document.getElementById(
        "cancelOrder"
    );

const submitButton =
    document.getElementById(
        "submitOrder"
    );

const modal =
    document.getElementById(
        "orderModal"
    );

const orderType =
    document.getElementById(
        "orderType"
    );

if (closeButton) {

    closeButton.addEventListener(
        "click",
        closeTradeOrder
    );
}

if (cancelButton) {

    cancelButton.addEventListener(
        "click",
        closeTradeOrder
    );
}

if (submitButton) {

    submitButton.addEventListener(
        "click",
        submitTradeOrder
    );
}

if (orderType) {

    orderType.addEventListener(
        "change",
        updateOrderTypeFields
    );
}

if (modal) {

    modal.addEventListener(
        "click",
        event => {

            if (
                event.target ===
                modal
            ) {

                closeTradeOrder();
            }
        }
    );
}

document.addEventListener(
    "keydown",
    event => {

        if (
            event.key ===
            "Escape"
        ) {

            closeTradeOrder();
        }
    }
);


}

/* ============================================================

* ERROR DISPLAY
* ============================================================ */

function renderDataUnavailable(
message
) {


const body =
    document.getElementById(
        "trades"
    );

const noTrades =
    document.getElementById(
        "noTrades"
    );

const tradeCount =
    document.getElementById(
        "tradeCount"
    );

const updated =
    document.getElementById(
        "updated"
    );

if (updated) {

    updated.textContent =
        "Data unavailable";
}

if (body) {

    body.innerHTML = `
        <tr>
            <td colspan="9">
                ${escapeHtml(
                    message
                )}
            </td>
        </tr>
    `;
}

if (tradeCount) {

    tradeCount.textContent =
        "0 trades";
}

if (noTrades) {

    noTrades.hidden =
        false;
}


}

/* ============================================================

* UTILITIES
* ============================================================ */

function toNumber(
value
) {


if (
    value === null ||
    value === undefined ||
    value === ""
) {

    return null;
}

const number =
    Number(value);

return Number.isFinite(
    number
)
    ? number
    : null;


}

function money(
value
) {


if (
    value === null ||
    value === undefined ||
    value === ""
) {

    return "—";
}

const number =
    Number(value);

if (
    !Number.isFinite(
        number
    )
) {

    return "—";
}

return number < 1
    ? "$" + number.toFixed(4)
    : "$" + number.toFixed(2);


}

function escapeHtml(
value
) {


return String(
    value ?? ""
)
    .replaceAll(
        "&",
        "&amp;"
    )
    .replaceAll(
        "<",
        "&lt;"
    )
    .replaceAll(
        ">",
        "&gt;"
    )
    .replaceAll(
        '"',
        "&quot;"
    )
    .replaceAll(
        "'",
        "&#039;"
    );


}

/* ============================================================

* AUTO REFRESH
* ============================================================ */

setInterval(
async () => {


    if (
        !selectedDate
    ) {
        return;
    }

    try {

        const index =
            await getJSON(
                "analysis/index.json"
            );

        window.__tradesIndex =
            index;

        await loadTradesForDate(
            selectedDate,
            getRequestedTicker()
        );

    } catch (error) {

        console.error(
            "Failed to refresh trade data:",
            error
        );
    }

},
60000


);

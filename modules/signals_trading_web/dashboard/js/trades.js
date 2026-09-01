"use strict";

/*

* ============================================================
* TRADES PAGE
* ============================================================
*
* Data structure:
*
* data/
* analysis/
* 
  index.json
  
* 
  TICKER/
  
* 
    YYYY-MM-DD_analysis_latest.json
  
* 
    YYYY-MM-DD_trades.json
  
*
* The date selector is populated from analysis/index.json.
*
* The selected date determines the actual JSON file loaded.
*
* ============================================================
  */

let allTrades = [];

let sortColumn = "score";
let sortDirection = "desc";

let selectedTrade = null;

let selectedDate = null;

const ANALYSIS_DATA_PATH =
"data/analysis";

const ANALYSIS_INDEX_PATH =
`${ANALYSIS_DATA_PATH}/index.json`;

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

* URL PARAMETERS
* ============================================================ */

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

function getRequestedDate() {


const params =
    new URLSearchParams(
        window.location.search
    );

const requestedDate =
    params.get("date");

if (
    requestedDate &&
    /^\d{4}-\d{2}-\d{2}$/.test(
        requestedDate
    )
) {
    return requestedDate;
}

return null;


}

/* ============================================================

* DATE HELPERS
* ============================================================ */

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


if (!isValidDateString(date)) {
    return date;
}

const parts =
    date.split("-");

const year =
    parts[0];

const month =
    Number(parts[1]);

const day =
    Number(parts[2]);

const dateObject =
    new Date(
        Number(year),
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

* DATA URL
* ============================================================ */

function getTradeDataUrl(
ticker,
date
) {


return (
    `${ANALYSIS_DATA_PATH}/` +
    `${encodeURIComponent(ticker)}/` +
    `${encodeURIComponent(date)}_trades.json`
);


}

/* ============================================================

* INDEX LOADING
* ============================================================ */

async function loadAnalysisIndex() {


const response =
    await fetch(
        `${ANALYSIS_INDEX_PATH}?t=${Date.now()}`,
        {
            cache: "no-store"
        }
    );

if (!response.ok) {
    throw new Error(
        `analysis/index.json HTTP ${response.status}`
    );
}

return response.json();


}

/*

* Extract the available dates for a ticker.
*
* This accepts the established index structure while also
* tolerating the common array/object representations.
  */
  function getAvailableDates(
  index,
  ticker
  ) {

  if (!index) {
  return [];
  }

  const upperTicker =
  ticker.toUpperCase();

  let tickerData = null;

  if (
  index.tickers &&
  typeof index.tickers === "object"
  ) {
  tickerData =
  index.tickers[upperTicker] ||
  index.tickers[ticker];
  }

  if (!tickerData && index[upperTicker]) {
  tickerData =
  index[upperTicker];
  }

  if (!tickerData) {
  return [];
  }

  let dates = [];

  if (
  Array.isArray(tickerData)
  ) {
  dates = tickerData;
  }

  else if (
  Array.isArray(
  tickerData.dates
  )
  ) {
  dates =
  tickerData.dates;
  }

  else if (
  Array.isArray(
  tickerData.available_dates
  )
  ) {
  dates =
  tickerData.available_dates;
  }

  else if (
  Array.isArray(
  tickerData.analysis_dates
  )
  ) {
  dates =
  tickerData.analysis_dates;
  }

  /*

  * Some index formats may expose files instead of
  * explicit dates.
    */
    else if (
    Array.isArray(
    tickerData.files
    )
    ) {

    dates =
    tickerData.files
    .map(
    file => {

    
                 const match =
                     String(file)
                         .match(
                             /(\d{4}-\d{2}-\d{2})/
                         );

                 return match
                     ? match[1]
                     : null;
             }
         )
         .filter(Boolean);
    

  }

  return [
  ...new Set(
  dates
  .map(
  date =>
  String(date)
  .trim()
  )
  .filter(
  isValidDateString
  )
  )
  ].sort(
  (a, b) =>
  b.localeCompare(a)
  );
  }

/* ============================================================

* DATE SELECTOR
* ============================================================ */

function getDateSelector() {


return document.getElementById(
    "tradeDate"
);


}

function createDateSelector() {


let selector =
    getDateSelector();

if (selector) {
    return selector;
}

/*
 * Look for a natural controls area first.
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

if (!container) {

    container =
        document.querySelector(
            "main"
        );
}

if (!container) {
    return null;
}

const wrapper =
    document.createElement(
        "div"
    );

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

selector =
    document.createElement(
        "select"
    );

selector.id =
    "tradeDate";

selector.name =
    "tradeDate";

selector.setAttribute(
    "aria-label",
    "Trade date"
);

wrapper.appendChild(
    label
);

wrapper.appendChild(
    selector
);

/*
 * Insert at the beginning so the date selector
 * is always visible with the other controls.
 */
container.prepend(
    wrapper
);

return selector;


}

function populateDateSelector(
dates,
requestedDate
) {


const selector =
    createDateSelector();

if (!selector) {
    console.warn(
        "Trade date selector could not be created."
    );

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

/*
 * Use the URL date when it exists and is available.
 * Otherwise default to the newest available date.
 */
const dateToSelect =
    requestedDate &&
    dates.includes(
        requestedDate
    )
        ? requestedDate
        : dates[0];

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
            dateToSelect
        ) {
            option.selected =
                true;
        }

        selector.appendChild(
            option
        );
    }
);

selectedDate =
    dateToSelect;

selector.addEventListener(
    "change",
    () => {

        const newDate =
            selector.value;

        if (
            !isValidDateString(
                newDate
            )
        ) {
            return;
        }

        selectedDate =
            newDate;

        updateUrlDate(
            newDate
        );

        load(
            getRequestedTicker(),
            newDate
        );
    }
);

return selector;


}

/* ============================================================

* URL DATE UPDATE
* ============================================================ */

function updateUrlDate(
date
) {


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

* MAIN INITIALIZATION
* ============================================================ */

async function initializeTrades() {


const ticker =
    getRequestedTicker();

if (!ticker) {

    renderDataUnavailable(
        "No ticker was specified."
    );

    return;
}

try {

    const index =
        await loadAnalysisIndex();

    const dates =
        getAvailableDates(
            index,
            ticker
        );

    const requestedDate =
        getRequestedDate();

    const selector =
        populateDateSelector(
            dates,
            requestedDate
        );

    if (!dates.length) {

        renderDataUnavailable(
            `No trade dates are available for ${ticker}.`
        );

        return;
    }

    /*
     * populateDateSelector() determines the actual date
     * selected from the URL or newest available date.
     */
    const date =
        selector &&
        selector.value
            ? selector.value
            : (
                requestedDate &&
                dates.includes(
                    requestedDate
                )
                    ? requestedDate
                    : dates[0]
            );

    selectedDate =
        date;

    updateUrlDate(
        date
    );

    await load(
        ticker,
        date
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

* LOAD TRADES
* ============================================================ */

async function load(
ticker,
date
) {


if (!ticker) {
    return;
}

if (
    !date ||
    !isValidDateString(date)
) {
    renderDataUnavailable(
        "No valid trade date was selected."
    );

    return;
}

selectedDate =
    date;

const dataUrl =
    getTradeDataUrl(
        ticker,
        date
    );

try {

    const response =
        await fetch(
            `${dataUrl}?t=${Date.now()}`,
            {
                cache: "no-store"
            }
        );

    if (!response.ok) {

        throw new Error(
            `${dataUrl} HTTP ${response.status}`
        );
    }

    const data =
        await response.json();

    const updated =
        document.getElementById(
            "updated"
        );

    if (updated) {

        updated.textContent =
            data.generated_at ||
            date;
    }

    allTrades =
        Array.isArray(
            data.trades
        )
            ? data.trades
            : [];

    renderTrades();

} catch (error) {

    const updated =
        document.getElementById(
            "updated"
        );

    if (updated) {
        updated.textContent =
            "Data unavailable";
    }

    allTrades = [];

    renderDataUnavailable(
        `Unable to load ${ticker} trades for ${formatDateLabel(date)}.`
    );

    console.error(
        "Failed to load ticker trade data:",
        error
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
                    trade.ticker || ""
                ).toUpperCase();

            const tradeDirection =
                String(
                    trade.direction || ""
                ).toUpperCase();

            const tradeStatus =
                String(
                    trade.status || ""
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
                        trade.ticker || ""
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
                        : score.toFixed(2)
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
                        trade.ticker || ""
                    )
                        .trim()
                        .toUpperCase();

                if (!ticker) {
                    return;
                }

                /*
                 * IMPORTANT:
                 * Use the date currently being displayed.
                 * Do NOT recalculate today's date.
                 */
                const date =
                    selectedDate ||
                    getRequestedDate();

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
        trade.ticker || ""
    ).toUpperCase();

const direction =
    String(
        trade.direction || ""
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
    money(trade.entry);

document.getElementById(
    "summaryCurrent"
).textContent =
    money(trade.current_price);

document.getElementById(
    "summaryStop"
).textContent =
    money(trade.stop);

document.getElementById(
    "summaryTarget"
).textContent =
    money(trade.target);

const score =
    toNumber(
        trade.score
    );

document.getElementById(
    "summaryScore"
).textContent =
    score === null
        ? "—"
        : score.toFixed(2);

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
    !Number.isFinite(quantity) ||
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
                selectedTrade.ticker,

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

* DISPLAY ERROR
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

return Number.isFinite(number)
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

if (!Number.isFinite(number)) {
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
() => {


    const ticker =
        getRequestedTicker();

    if (
        ticker &&
        selectedDate
    ) {

        load(
            ticker,
            selectedDate
        );
    }
},
60000


);

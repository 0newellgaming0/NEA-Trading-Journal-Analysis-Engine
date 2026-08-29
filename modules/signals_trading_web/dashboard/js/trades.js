"use strict";

let allTrades = [];

let sortColumn = "score";
let sortDirection = "desc";

let selectedTrade = null;

const ANALYSIS_DATA_PATH =
"data/analysis";

if (
    document.readyState ===
    "loading"
) {
    document.addEventListener(
        "DOMContentLoaded",
        initializeTrades
    );
} else {
    initializeTrades();
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

return `${year}-${month}-${day}`;


}

function getTradeDataUrl(
ticker
) {
return (
`${ANALYSIS_DATA_PATH}/` +
`${encodeURIComponent(ticker)}/trades.json`
);
}

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
    await load(
        ticker
    );

    initializeSorting();
    initializeFilters();
    initializeOrderDialog();

} catch (error) {

    console.error(
        "Failed to initialize trade data:",
        error
    );
}


}

async function load(
ticker
) {
const date =
getRequestedDate();


const dataUrl =
    getTradeDataUrl(
        ticker
    );

try {
    const response =
        await fetch(
            `${dataUrl}?date=${encodeURIComponent(
                date
            )}&t=${Date.now()}`,
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

    renderDataUnavailable(
        `Unable to load ${ticker} trade data.`
    );

    console.error(
        "Failed to load ticker trade data:",
        error
    );
}


}

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
                        trade.ticker || ""
                    )
                        .trim()
                        .toUpperCase();

                if (!ticker) {
                    return;
                }

                const date =
                    getRequestedDate();

                window.location.href =
                    `ticker-profile.html?ticker=${encodeURIComponent(
                        ticker
                    )}&date=${encodeURIComponent(
                        date
                    )}`;
            }
        );

        body.appendChild(row);
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

function openTradeOrder(
trade
) {


selectedTrade = trade;

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
).value = ticker;

document.getElementById(
    "orderSide"
).value = side;

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

selectedTrade = null;


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
        ticker: ticker,
        side: side,
        order_type: orderType,
        quantity: quantity,

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

setInterval(
() => {


    const ticker =
        getRequestedTicker();

    if (ticker) {
        load(ticker);
    }
},
60000


);

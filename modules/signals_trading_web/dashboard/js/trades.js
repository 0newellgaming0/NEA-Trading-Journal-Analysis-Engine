"use strict";

/*
 * ============================================================
 * TRADES PAGE
 * ============================================================
 *
 * PUBLIC STRUCTURE
 *
 * data/
 *   analysis/
 *     index.json
 *
 *     TICKER/
 *       YYYY-MM-DD_trades.json
 *
 * ============================================================
 *
 * DATE BEHAVIOR
 *
 * "" / All Dates
 *     -> load ALL published trade dates
 *
 * "YYYY-MM-DD"
 *     -> load ONLY that published date
 *
 * ?ticker=AAPL
 *     -> restrict loading to AAPL
 *
 * ?ticker=AAPL&date=YYYY-MM-DD
 *     -> load AAPL for that date
 *
 * ============================================================
 */


/* ============================================================
   STATE
   ============================================================ */

let allTrades = [];

let sortColumn = "score";
let sortDirection = "desc";

let selectedDate = "";

let availableDates = [];

let dateSelectorInitialized = false;


/* ============================================================
   PATHS
   ============================================================ */

const ANALYSIS_INDEX_PATH =
    "analysis/index.json";


/* ============================================================
   INITIALIZATION
   ============================================================ */

if (document.readyState === "loading") {

    document.addEventListener(
        "DOMContentLoaded",
        initializeTrades
    );

} else {

    initializeTrades();
}


/* ============================================================
   JSON LOADER
   ============================================================ */

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
   URL PARAMETERS
   ============================================================ */

function getRequestedDate() {

    const params =
        new URLSearchParams(
            window.location.search
        );

    const date =
        params.get("date");

    if (
        date &&
        isValidDateString(date)
    ) {
        return date;
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
   DATE HELPERS
   ============================================================ */

function isValidDateString(value) {

    return (
        typeof value === "string" &&
        /^\d{4}-\d{2}-\d{2}$/.test(value)
    );
}


function formatDateLabel(date) {

    if (!isValidDateString(date)) {
        return date;
    }

    const [
        year,
        month,
        day
    ] = date.split("-").map(Number);

    /*
     * Use UTC here so the displayed date cannot shift
     * backward/forward because of the browser timezone.
     */
    const dateObject =
        new Date(
            Date.UTC(
                year,
                month - 1,
                day
            )
        );

    return dateObject.toLocaleDateString(
        undefined,
        {
            timeZone: "UTC",
            year: "numeric",
            month: "long",
            day: "numeric"
        }
    );
}


/* ============================================================
   INDEX DATE EXTRACTION
   ============================================================ */

function getAvailableDates(index) {

    const dateSet =
        new Set();

    const tickers =
        index &&
        typeof index.tickers === "object" &&
        index.tickers !== null
            ? index.tickers
            : {};

    Object.values(tickers).forEach(
        value => {

            /*
             * Normal structure:
             *
             * ticker: [
             *     "2026-08-29",
             *     "2026-08-30"
             * ]
             */
            if (Array.isArray(value)) {

                value.forEach(
                    date => {

                        if (
                            isValidDateString(date)
                        ) {
                            dateSet.add(date);
                        }
                    }
                );

                return;
            }

            /*
             * Also tolerate:
             *
             * ticker: {
             *     dates: [...]
             * }
             */
            if (
                value &&
                typeof value === "object"
            ) {

                const dates =
                    Array.isArray(value.dates)
                        ? value.dates
                        : [];

                dates.forEach(
                    date => {

                        if (
                            isValidDateString(date)
                        ) {
                            dateSet.add(date);
                        }
                    }
                );
            }
        }
    );

    return Array.from(dateSet).sort(
        (a, b) =>
            b.localeCompare(a)
    );
}


/* ============================================================
   FIND / CREATE DATE SELECTOR
   ============================================================ */

function findDateSelector() {

    const existing =
        document.getElementById(
            "tradeDate"
        );

    if (existing) {
        return existing;
    }

    const container =
        document.querySelector(
            ".trade-controls"
        );

    if (!container) {

        console.error(
            "Cannot create trade date selector: .trade-controls not found."
        );

        return null;
    }

    const wrapper =
        document.createElement("div");

    wrapper.id =
        "tradeDateContainer";

    wrapper.className =
        "trade-date-control";

    const label =
        document.createElement("label");

    label.htmlFor =
        "tradeDate";

    label.textContent =
        "Trade Date";

    const selector =
        document.createElement("select");

    selector.id =
        "tradeDate";

    selector.name =
        "tradeDate";

    selector.setAttribute(
        "aria-label",
        "Trade Date"
    );

    wrapper.appendChild(label);
    wrapper.appendChild(selector);

    container.prepend(wrapper);

    return selector;
}


/* ============================================================
   INITIALIZE DATE SELECTOR
   ============================================================ */

function initializeDateSelector(
    dates,
    preserveSelection = false
) {

    const selector =
        findDateSelector();

    if (!selector) {
        return null;
    }

    const previousSelection =
        selectedDate;

    selector.innerHTML = "";

    /*
     * ALWAYS provide All Dates.
     */
    const allDatesOption =
        document.createElement("option");

    allDatesOption.value = "";

    allDatesOption.textContent =
        "All Dates";

    selector.appendChild(
        allDatesOption
    );

    if (!dates.length) {

        selector.disabled = true;

        selectedDate = "";

        selector.value = "";

        updateUrlDate("");

        return selector;
    }

    selector.disabled = false;

    const requestedDate =
        getRequestedDate();

    /*
     * Selection priority:
     *
     * 1. Existing selection during refresh
     * 2. Explicit ?date=
     * 3. All Dates
     */
    if (
        preserveSelection &&
        (
            previousSelection === "" ||
            dates.includes(previousSelection)
        )
    ) {

        selectedDate =
            previousSelection;

    } else if (
        requestedDate &&
        dates.includes(requestedDate)
    ) {

        selectedDate =
            requestedDate;

    } else {

        selectedDate = "";
    }

    dates.forEach(
        date => {

            const option =
                document.createElement("option");

            option.value =
                date;

            option.textContent =
                formatDateLabel(date);

            selector.appendChild(option);
        }
    );

    selector.value =
        selectedDate;

    /*
     * Attach exactly once.
     */
    if (!dateSelectorInitialized) {

        selector.addEventListener(
            "change",
            async () => {

                selectedDate =
                    selector.value;

                updateUrlDate(
                    selectedDate
                );

                await reloadCurrentTrades();
            }
        );

        dateSelectorInitialized = true;
    }

    updateUrlDate(
        selectedDate
    );

    return selector;
}


/* ============================================================
   URL DATE SYNCHRONIZATION
   ============================================================ */

function updateUrlDate(date) {

    const url =
        new URL(
            window.location.href
        );

    if (date === "") {

        url.searchParams.delete("date");

    } else if (
        isValidDateString(date)
    ) {

        url.searchParams.set(
            "date",
            date
        );
    }

    window.history.replaceState(
        {},
        "",
        url
    );
}


/* ============================================================
   GET PUBLISHED TICKERS
   ============================================================ */

function getIndexedTickers(index) {

    if (
        !index ||
        !index.tickers ||
        typeof index.tickers !== "object"
    ) {
        return {};
    }

    return index.tickers;
}


/* ============================================================
   GET TICKER PUBLISHED DATES
   ============================================================ */

function getTickerDates(
    ticker,
    index
) {

    const tickers =
        getIndexedTickers(index);

    const value =
        tickers[ticker];

    if (Array.isArray(value)) {
        return value.filter(
            isValidDateString
        );
    }

    if (
        value &&
        typeof value === "object" &&
        Array.isArray(value.dates)
    ) {

        return value.dates.filter(
            isValidDateString
        );
    }

    return [];
}


/* ============================================================
   TRADE FILE PATH
   ============================================================ */

function getTradeFilePath(
    ticker,
    date
) {

    return (
        "analysis/" +
        encodeURIComponent(ticker) +
        "/" +
        date +
        "_trades.json"
    );
}


/* ============================================================
   EXTRACT TRADES FROM JSON
   ============================================================ */

function extractTrades(data) {

    if (Array.isArray(data)) {
        return data;
    }

    if (
        data &&
        Array.isArray(data.trades)
    ) {
        return data.trades;
    }

    /*
     * Also tolerate:
     *
     * {
     *   data: {
     *      trades: [...]
     *   }
     * }
     */
    if (
        data &&
        data.data &&
        Array.isArray(data.data.trades)
    ) {
        return data.data.trades;
    }

    return [];
}


/* ============================================================
   TRADE DATE
   ============================================================ */

function getTradeDate(trade) {

    if (
        !trade ||
        typeof trade !== "object"
    ) {
        return null;
    }

    /*
     * ONLY actual trade-date fields are preferred.
     */
    const value =
        trade.trade_date ??
        trade.tradeDate ??
        trade.execution_date ??
        trade.executionDate ??
        trade.entry_date ??
        trade.entryDate ??
        trade.date;

    if (
        value === null ||
        value === undefined ||
        value === ""
    ) {
        return null;
    }

    const text =
        String(value).trim();

    const match =
        text.match(
            /^(\d{4}-\d{2}-\d{2})/
        );

    if (match) {
        return match[1];
    }

    return null;
}


/* ============================================================
   TRADE TIMESTAMP
   ============================================================ */

function getTradeTimestamp(trade) {

    if (
        !trade ||
        typeof trade !== "object"
    ) {
        return 0;
    }

    const value =
        trade.timestamp ??
        trade.trade_timestamp ??
        trade.tradeTimestamp ??
        trade.created_at ??
        trade.createdAt ??
        trade.updated_at ??
        trade.updatedAt;

    if (
        value === null ||
        value === undefined ||
        value === ""
    ) {
        return 0;
    }

    const timestamp =
        new Date(value).getTime();

    return Number.isFinite(timestamp)
        ? timestamp
        : 0;
}


/* ============================================================
   LOAD ONE TICKER / ONE DATE
   ============================================================ */

async function loadTickerDate(
    ticker,
    date
) {

    const file =
        getTradeFilePath(
            ticker,
            date
        );

    try {

        const data =
            await getJSON(file);

        const trades =
            extractTrades(data);

        return trades.map(
            trade => ({
                ...trade,

                _ticker:
                    String(
                        trade.ticker ||
                        ticker
                    )
                        .trim()
                        .toUpperCase(),

                _date:
                    getTradeDate(trade) ||
                    date
            })
        );

    } catch (error) {

        /*
         * A missing date file should not kill the entire
         * table. It simply means that ticker/date has no
         * published trade file.
         */
        console.warn(
            `No trade file for ${ticker} ${date}:`,
            error.message
        );

        return [];
    }
}


/* ============================================================
   LOAD TRADES
   ============================================================ */

async function loadTradesForDate(
    date,
    requestedTicker = null
) {

    const index =
        window.__tradesIndex;

    const tickers =
        getIndexedTickers(index);

    const tickerNames =
        Object.keys(tickers);

    const tickersToLoad =
        requestedTicker
            ? tickerNames.filter(
                ticker =>
                    ticker.toUpperCase() ===
                    requestedTicker
            )
            : tickerNames;

    const loadedTrades = [];

    /*
     * ========================================================
     * ALL DATES
     * ========================================================
     *
     * Load every published date for every ticker.
     */
    if (date === "") {

        for (
            const ticker of tickersToLoad
        ) {

            const tickerDates =
                getTickerDates(
                    ticker,
                    index
                );

            for (
                const publishedDate of tickerDates
            ) {

                const trades =
                    await loadTickerDate(
                        ticker,
                        publishedDate
                    );

                loadedTrades.push(
                    ...trades
                );
            }
        }

    } else {

        /*
         * ====================================================
         * SPECIFIC DATE
         * ====================================================
         */

        for (
            const ticker of tickersToLoad
        ) {

            const tickerDates =
                getTickerDates(
                    ticker,
                    index
                );

            if (
                !tickerDates.includes(date)
            ) {
                continue;
            }

            const trades =
                await loadTickerDate(
                    ticker,
                    date
                );

            /*
             * If the published file contains multiple
             * records, retain only records belonging to
             * the selected date.
             */
            const matchingTrades =
                trades.filter(
                    trade =>
                        !getTradeDate(trade) ||
                        getTradeDate(trade) === date
                );

            /*
             * If multiple trade records exist for the
             * same ticker/date, retain them all.
             *
             * The trade page is a trade-history table,
             * so we should NOT silently delete records.
             */
            loadedTrades.push(
                ...matchingTrades
            );
        }
    }

    /*
     * Newest trade first before the table sort is applied.
     */
    loadedTrades.sort(
        (a, b) =>
            getTradeTimestamp(b) -
            getTradeTimestamp(a)
    );

    allTrades =
        loadedTrades;

    renderTrades();
}


/* ============================================================
   RELOAD CURRENT VIEW
   ============================================================ */

async function reloadCurrentTrades() {

    try {

        await loadTradesForDate(
            selectedDate,
            getRequestedTicker()
        );

    } catch (error) {

        console.error(
            "Failed to reload trades:",
            error
        );

        renderDataUnavailable(
            "Unable to load trades."
        );
    }
}


/* ============================================================
   INITIALIZE PAGE
   ============================================================ */

async function initializeTrades() {

    try {

        const index =
            await getJSON(
                ANALYSIS_INDEX_PATH
            );

        window.__tradesIndex =
            index;

        availableDates =
            getAvailableDates(index);

        initializeDateSelector(
            availableDates
        );

        /*
         * IMPORTANT:
         *
         * Do not force a date here.
         *
         * selectedDate is either:
         *
         *     ""
         *     or
         *     ?date=YYYY-MM-DD
         */
        await loadTradesForDate(
            selectedDate,
            getRequestedTicker()
        );

        initializeSorting();

        initializeFilters();

    } catch (error) {

        console.error(
            "Failed to initialize trades:",
            error
        );

        renderDataUnavailable(
            "Unable to load trade history."
        );
    }
}


/* ============================================================
   RENDER TABLE
   ============================================================ */

function renderTrades() {

    const body =
        document.getElementById("trades");

    const noTrades =
        document.getElementById("noTrades");

    const tradeCount =
        document.getElementById("tradeCount");

    if (!body) {

        console.error(
            "#trades table body was not found."
        );

        return;
    }

    const searchInput =
        document.getElementById("tickerSearch");

    const directionFilter =
        document.getElementById("directionFilter");

    const statusFilter =
        document.getElementById("statusFilter");

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

                return (
                    (!search ||
                        ticker.includes(search)) &&
                    (!direction ||
                        tradeDirection === direction) &&
                    (!status ||
                        tradeStatus === status)
                );
            }
        );

    /*
     * ========================================================
     * SORT
     * ========================================================
     */

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

            let comparison;

            if (
                typeof aValue === "number" &&
                typeof bValue === "number"
            ) {

                comparison =
                    aValue - bValue;

            } else {

                comparison =
                    String(aValue).localeCompare(
                        String(bValue),
                        undefined,
                        {
                            numeric: true,
                            sensitivity: "base"
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

    /*
     * ========================================================
     * BUILD TABLE
     * ========================================================
     */

    body.innerHTML = "";

    trades.forEach(
        trade => {

            const row =
                document.createElement("tr");

            row.className =
                "trade-row";

            const score =
                toNumber(trade.score);

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
                        trade.direction || "—"
                    )}
                </td>

                <td>
                    ${escapeHtml(
                        trade.setup || "—"
                    )}
                </td>

                <td>
                    ${money(trade.entry)}
                </td>

                <td>
                    ${money(trade.current_price)}
                </td>

                <td>
                    ${money(trade.stop)}
                </td>

                <td>
                    ${money(trade.target)}
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
                            trade.status || "—"
                        )}
                    </span>
                </td>
            `;

            /*
             * Single-click ticker navigation.
             */
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

                    /*
                     * For All Dates, use this individual
                     * trade's actual date.
                     *
                     * For a selected date, use selectedDate.
                     */
                    const date =
                        selectedDate ||
                        trade._date ||
                        getTradeDate(trade);

                    let url =
                        "ticker-profile.html" +
                        "?ticker=" +
                        encodeURIComponent(ticker);

                    if (
                        isValidDateString(date)
                    ) {

                        url +=
                            "&date=" +
                            encodeURIComponent(date);
                    }

                    window.location.href =
                        url;
                }
            );

            body.appendChild(row);
        }
    );

    /*
     * ========================================================
     * COUNTS
     * ========================================================
     */

    if (tradeCount) {

        tradeCount.textContent =
            `${trades.length} of ${allTrades.length} trades`;
    }

    if (noTrades) {

        noTrades.hidden =
            trades.length !== 0;
    }

    updateSortHeaders();

    updateDisplayedDate();
}


/* ============================================================
   DISPLAY DATE
   ============================================================ */

function updateDisplayedDate() {

    const updated =
        document.getElementById("updated");

    if (!updated) {
        return;
    }

    if (selectedDate === "") {

        updated.textContent =
            "All Dates";

        return;
    }

    updated.textContent =
        formatDateLabel(
            selectedDate
        );
}


/* ============================================================
   SORTING
   ============================================================ */

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
        numericColumns.includes(column)
    ) {

        const value =
            toNumber(trade[column]);

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
                            sortColumn === column
                        ) {

                            sortDirection =
                                sortDirection === "asc"
                                    ? "desc"
                                    : "asc";

                        } else {

                            sortColumn =
                                column;

                            sortDirection =
                                column === "score"
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
   FILTERS
   ============================================================ */

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
   ERROR DISPLAY
   ============================================================ */

function renderDataUnavailable(message) {

    const body =
        document.getElementById("trades");

    const noTrades =
        document.getElementById("noTrades");

    const tradeCount =
        document.getElementById("tradeCount");

    const updated =
        document.getElementById("updated");

    if (updated) {
        updated.textContent =
            "Data unavailable";
    }

    if (body) {

        body.innerHTML = `
            <tr>
                <td colspan="9">
                    ${escapeHtml(message)}
                </td>
            </tr>
        `;
    }

    if (tradeCount) {
        tradeCount.textContent =
            "0 trades";
    }

    if (noTrades) {
        noTrades.hidden = false;
    }
}


/* ============================================================
   UTILITIES
   ============================================================ */

function toNumber(value) {

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


function money(value) {

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


function escapeHtml(value) {

    return String(value ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}


/* ============================================================
   AUTO REFRESH
   ============================================================ */

setInterval(
    async () => {

        try {

            const index =
                await getJSON(
                    ANALYSIS_INDEX_PATH
                );

            const newDates =
                getAvailableDates(index);

            const datesChanged =
                JSON.stringify(newDates) !==
                JSON.stringify(availableDates);

            window.__tradesIndex =
                index;

            if (datesChanged) {

                availableDates =
                    newDates;

                /*
                 * Preserve the user's current selection.
                 */
                initializeDateSelector(
                    availableDates,
                    true
                );
            }

            /*
             * IMPORTANT:
             *
             * Never reset selectedDate here.
             *
             * This allows:
             *
             *     All Dates
             *     selected date
             *
             * to survive refresh.
             */
            await reloadCurrentTrades();

        } catch (error) {

            console.error(
                "Failed to refresh trade data:",
                error
            );
        }

    },
    60000
);
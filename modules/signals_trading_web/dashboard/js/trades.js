"use strict";

/* ============================================================
   NEA28V1 TRADES PAGE
   ============================================================

   AUTHORITATIVE PUBLIC DATA STRUCTURE

   data/
       analysis/
           index.json
           TICKER/
               trades.json

   DATE BEHAVIOR

   Default:
       -> TODAY only

   ?date=YYYY-MM-DD:
       -> only trades for that selected date

   ?ticker=AAPL:
       -> restrict loading to AAPL

   ?ticker=AAPL&date=YYYY-MM-DD:
       -> AAPL trade for that actual date

   For a selected date:
       -> ticker must be published for that date
       -> actual trade date must equal selected date
       -> latest trade for ticker/date is retained

   IMPORTANT:
       The page does NOT default to All Dates.
       Today is the authoritative initial selection.
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

const ANALYSIS_INDEX_URL =
    "data/analysis/index.json";

/* ============================================================
   INITIALIZATION
============================================================ */

document.addEventListener(
    "DOMContentLoaded",
    initializeTrades
);

/* ============================================================
   GENERIC JSON LOADER
============================================================ */

async function getJSON(file) {

    const response =
        await fetch(
            `${file}?t=${Date.now()}`,
            {
                cache: "no-store"
            }
        );

    if (!response.ok) {

        throw new Error(
            `Unable to load ${file}: ${response.status}`
        );
    }

    return await response.json();
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

function getTodayDateKey() {

    const now =
        new Date();

    return [
        now.getFullYear(),
        String(
            now.getMonth() + 1
        ).padStart(2, "0"),
        String(
            now.getDate()
        ).padStart(2, "0")
    ].join("-");
}

function formatDateLabel(date) {

    if (
        !isValidDateString(date)
    ) {
        return date;
    }

    const [
        year,
        month,
        day
    ] =
        date.split("-").map(Number);

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
   DATE EXTRACTION
============================================================ */

function getTradeDate(trade) {

    const raw =
        trade &&
        trade.raw
            ? trade.raw
            : trade;

    if (
        !raw ||
        typeof raw !== "object"
    ) {
        return null;
    }

    const dateValue =
        firstValue(
            raw.trade_date,
            raw.tradeDate,
            raw.date,
            raw.created_date,
            raw.createdDate,
            raw.timestamp,
            raw.generated_at,
            raw.generatedAt,
            raw.updated_at,
            raw.updatedAt
        );

    if (!dateValue) {
        return null;
    }

    const text =
        String(
            dateValue
        ).trim();

    /*
     * Preserve an explicit YYYY-MM-DD prefix.
     *
     * This is important for publication timestamps such as:
     *
     * 2026-09-01T04:15:22
     */
    const directMatch =
        text.match(
            /^(\d{4}-\d{2}-\d{2})/
        );

    if (directMatch) {
        return directMatch[1];
    }

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
        ).padStart(2, "0"),
        String(
            parsed.getDate()
        ).padStart(2, "0")
    ].join("-");
}

function getTradeTimestamp(trade) {

    const raw =
        trade &&
        trade.raw
            ? trade.raw
            : trade;

    if (
        !raw ||
        typeof raw !== "object"
    ) {
        return 0;
    }

    const timestamp =
        firstValue(
            raw.trade_date,
            raw.tradeDate,
            raw.timestamp,
            raw.generated_at,
            raw.generatedAt,
            raw.updated_at,
            raw.updatedAt,
            raw.created_at,
            raw.createdAt
        );

    if (!timestamp) {
        return 0;
    }

    const value =
        new Date(
            timestamp
        ).getTime();

    return Number.isFinite(value)
        ? value
        : 0;
}

/* ============================================================
   NORMALIZATION
============================================================ */

function normalizeTradeData(data) {

    let source;

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

    } else {

        source = [];
    }

    return source
        .map(
            normalizeTrade
        )
        .filter(Boolean);
}

function normalizeTrade(trade) {

    if (
        !trade ||
        typeof trade !== "object"
    ) {
        return null;
    }

    const ticker =
        firstValue(
            trade.ticker,
            trade.symbol,
            trade.Ticker,
            trade.Symbol
        );

    if (!ticker) {
        return null;
    }

    const entry =
        numericValue(
            firstValue(
                trade.entry,
                trade.entry_price,
                trade.Entry
            )
        );

    const stop =
        numericValue(
            firstValue(
                trade.stop,
                trade.stop_loss,
                trade.Stop
            )
        );

    const target =
        numericValue(
            firstValue(
                trade.target,
                trade.target_price,
                trade.Target
            )
        );

    const score =
        numericValue(
            firstValue(
                trade.score,
                trade.rank_score,
                trade.Score
            )
        );

    return {

        ticker:
            String(
                ticker
            ).toUpperCase(),

        direction:
            firstValue(
                trade.direction,
                trade.side,
                trade.Direction
            ) || "—",

        setup:
            firstValue(
                trade.setup,
                trade.setup_type,
                trade.Setup
            ) || "Trade Setup",

        entry,

        stop,

        target,

        score,

        status:
            firstValue(
                trade.status,
                trade.Status
            ) || "—",

        current_price:
            numericValue(
                firstValue(
                    trade.current_price,
                    trade.currentPrice,
                    trade.price,
                    trade.Price
                )
            ),

        raw:
            trade
    };
}

/* ============================================================
   AVAILABLE DATES
============================================================ */

function getAvailableDates(index) {

    const dateSet =
        new Set();

    if (
        !index ||
        typeof index.tickers !== "object" ||
        index.tickers === null
    ) {
        return [];
    }

    Object.entries(
        index.tickers
    ).forEach(
        ([ticker, dates]) => {

            if (!Array.isArray(dates)) {
                return;
            }

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
    );

    return Array.from(
        dateSet
    ).sort(
        (a, b) =>
            b.localeCompare(a)
    );
}

/* ============================================================
   INITIAL DATE SELECTION
============================================================ */

/*
 * Determines the date that should actually be selected
 * when the page first loads.
 *
 * Priority:
 *
 * 1. Existing selection during refresh
 * 2. Explicit ?date=YYYY-MM-DD
 * 3. TODAY
 * 4. Latest available publication date
 *
 * There is intentionally NO "All Dates" default.
 */
function determineInitialDate(
    dates,
    preserveSelection = false
) {

    if (!Array.isArray(dates) || !dates.length) {
        return "";
    }

    const today =
        getTodayDateKey();

    const requestedDate =
        getRequestedDate();

    if (
        preserveSelection &&
        selectedDate &&
        dates.includes(
            selectedDate
        )
    ) {
        return selectedDate;
    }

    if (
        requestedDate &&
        dates.includes(
            requestedDate
        )
    ) {
        return requestedDate;
    }

    /*
     * TODAY IS THE DEFAULT.
     */
    if (
        dates.includes(
            today
        )
    ) {
        return today;
    }

    /*
     * If today's publication does not yet exist,
     * use the newest actually published date rather
     * than loading All Dates.
     */
    return dates[0];
}

/* ============================================================
   DATE SELECTOR
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
            "Trades page: .trade-controls was not found."
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
    dates,
    preserveSelection = false
) {

    const selector =
        findDateSelector();

    if (!selector) {
        return null;
    }

    selector.innerHTML =
        "";

    if (!dates.length) {

        selector.disabled =
            true;

        selectedDate =
            "";

        return selector;
    }

    selector.disabled =
        false;

    /*
     * Do NOT create All Dates as the default.
     *
     * The selector contains actual publication dates only.
     */
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

            selector.appendChild(
                option
            );
        }
    );

    selectedDate =
        determineInitialDate(
            dates,
            preserveSelection
        );

    selector.value =
        selectedDate;

    if (
        !dateSelectorInitialized
    ) {

        selector.addEventListener(
            "change",
            async () => {

                selectedDate =
                    selector.value;

                updateUrlDate(
                    selectedDate
                );

                try {

                    await loadTradesForDate(
                        selectedDate,
                        getRequestedTicker()
                    );

                } catch (error) {

                    console.error(
                        "Trades date selection error:",
                        error
                    );

                    renderDataUnavailable(
                        "Unable to load trades for the selected date."
                    );
                }
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
   URL DATE SYNCHRONIZATION
============================================================ */

function updateUrlDate(date) {

    const url =
        new URL(
            window.location.href
        );

    if (
        isValidDateString(date)
    ) {

        url.searchParams.set(
            "date",
            date
        );

    } else {

        url.searchParams.delete(
            "date"
        );
    }

    window.history.replaceState(
        {},
        "",
        url
    );
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

    if (
        !index ||
        typeof index.tickers !== "object" ||
        index.tickers === null
    ) {

        renderDataUnavailable(
            "Trade index unavailable."
        );

        return;
    }

    /*
     * A valid selected date is required.
     *
     * The page no longer has an All Dates default.
     */
    if (
        !isValidDateString(date)
    ) {

        renderDataUnavailable(
            "No published trade date is available."
        );

        return;
    }

    const tickerEntries =
        Object.entries(
            index.tickers
        );

    const entriesToLoad =
        requestedTicker
            ? tickerEntries.filter(
                ([ticker]) =>
                    ticker.toUpperCase() ===
                    requestedTicker
            )
            : tickerEntries;

    const loadedTrades =
        [];

    for (
        const [
            ticker,
            publishedDates
        ]
        of entriesToLoad
    ) {

        if (
            !Array.isArray(
                publishedDates
            )
        ) {
            continue;
        }

        /*
         * The authoritative index determines whether
         * this ticker was published for the selected date.
         */
        if (
            !publishedDates.includes(
                date
            )
        ) {
            continue;
        }

        const tradeFile =
            `data/analysis/${encodeURIComponent(
                ticker
            )}/trades.json`;

        try {

            const data =
                await getJSON(
                    tradeFile
                );

            /*
             * Same normalization contract as newsletter.js.
             */
            const trades =
                normalizeTradeData(
                    data
                );

            if (!trades.length) {
                continue;
            }

            /*
             * The publication file can contain historical
             * records, so the actual trade date must also
             * match the selected publication date.
             */
            const matchingTrades =
                trades.filter(
                    trade =>
                        getTradeDate(
                            trade
                        ) === date
                );

            if (!matchingTrades.length) {
                continue;
            }

            /*
             * Newest trade first.
             */
            matchingTrades.sort(
                (a, b) =>
                    getTradeTimestamp(b) -
                    getTradeTimestamp(a)
            );

            /*
             * Keep only the latest trade for this ticker
             * on the selected date.
             */
            const latest =
                matchingTrades[0];

            loadedTrades.push({

                ...latest,

                _ticker:
                    ticker.toUpperCase(),

                _date:
                    date,

                _analysisDate:
                    date
            });

        } catch (error) {

            console.warn(
                `Unable to load trades for ${ticker}:`,
                error
            );
        }
    }

    allTrades =
        loadedTrades;

    renderTrades();
}

/* ============================================================
   INITIALIZE PAGE
============================================================ */

async function initializeTrades() {

    try {

        const index =
            await getJSON(
                ANALYSIS_INDEX_URL
            );

        if (
            !index ||
            typeof index.tickers !== "object" ||
            index.tickers === null
        ) {

            throw new Error(
                "Analysis index does not contain a valid tickers object."
            );
        }

        window.__tradesIndex =
            index;

        availableDates =
            getAvailableDates(
                index
            );

        /*
         * This now selects TODAY by default.
         *
         * If today has not been published yet,
         * it selects the newest published date.
         *
         * It never defaults to All Dates.
         */
        const selector =
            initializeDateSelector(
                availableDates
            );

        if (selector) {

            selectedDate =
                selector.value;
        }

        await loadTradesForDate(
            selectedDate,
            getRequestedTicker()
        );

        initializeSorting();

        initializeFilters();

    } catch (error) {

        console.error(
            "NEA28V1 trades initialization error:",
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

                return (
                    (
                        !search ||
                        ticker.includes(
                            search
                        )
                    ) &&
                    (
                        !direction ||
                        tradeDirection ===
                            direction
                    ) &&
                    (
                        !status ||
                        tradeStatus ===
                            status
                    )
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

            let comparison;

            if (
                typeof aValue === "number" &&
                typeof bValue === "number"
            ) {

                comparison =
                    aValue -
                    bValue;

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

    body.innerHTML =
        "";

    trades.forEach(
        trade => {

            const row =
                document.createElement(
                    "tr"
                );

            row.className =
                "trade-row";

            const score =
                trade.score;

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
                    ${formatMoney(
                        trade.entry
                    )}
                </td>

                <td>
                    ${formatMoney(
                        trade.current_price
                    )}
                </td>

                <td>
                    ${formatMoney(
                        trade.stop
                    )}
                </td>

                <td>
                    ${formatMoney(
                        trade.target
                    )}
                </td>

                <td>
                    ${
                        Number.isFinite(score)
                            ? score.toFixed(2)
                            : "—"
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

                    const profileDate =
                        selectedDate ||
                        getTradeDate(
                            trade
                        );

                    let url =
                        `ticker-profile.html?ticker=${encodeURIComponent(
                            ticker
                        )}`;

                    if (
                        isValidDateString(
                            profileDate
                        )
                    ) {

                        url +=
                            `&date=${encodeURIComponent(
                                profileDate
                            )}`;
                    }

                    window.location.href =
                        url;
                }
            );

            body.appendChild(
                row
            );
        }
    );

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
        document.getElementById(
            "updated"
        );

    if (!updated) {
        return;
    }

    if (
        !isValidDateString(
            selectedDate
        )
    ) {

        updated.textContent =
            "No Published Date";

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
   ERROR / EMPTY STATE
============================================================ */

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
   UTILITIES
============================================================ */

function numericValue(value) {

    if (
        value === null ||
        value === undefined ||
        value === ""
    ) {
        return NaN;
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
}

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

function formatMoney(value) {

    if (
        !Number.isFinite(value)
    ) {
        return "—";
    }

    return value < 1
        ? `$${value.toFixed(4)}`
        : `$${value.toFixed(2)}`;
}

function firstValue(
    ...values
) {

    for (
        const value
        of values
    ) {

        if (
            value !== undefined &&
            value !== null &&
            value !== ""
        ) {
            return value;
        }
    }

    return null;
}

function escapeHtml(value) {

    return String(
        value ?? ""
    )
    .replace(
        /&/g,
        "&amp;"
    )
    .replace(
        /</g,
        "&lt;"
    )
    .replace(
        />/g,
        "&gt;"
    )
    .replace(
        /"/g,
        "&quot;"
    )
    .replace(
        /'/g,
        "&#039;"
    );
}

/* ============================================================
   AUTO REFRESH
============================================================ */

setInterval(
    async () => {

        try {

            const index =
                await getJSON(
                    ANALYSIS_INDEX_URL
                );

            if (
                !index ||
                typeof index.tickers !== "object" ||
                index.tickers === null
            ) {
                return;
            }

            window.__tradesIndex =
                index;

            const newDates =
                getAvailableDates(
                    index
                );

            const datesChanged =
                JSON.stringify(
                    newDates
                ) !==
                JSON.stringify(
                    availableDates
                );

            if (
                datesChanged
            ) {

                availableDates =
                    newDates;

                initializeDateSelector(
                    availableDates,
                    true
                );
            }

            /*
             * Reload the currently selected date.
             *
             * If the page was initially opened today,
             * selectedDate remains today.
             */
            await loadTradesForDate(
                selectedDate,
                getRequestedTicker()
            );

        } catch (error) {

            console.error(
                "NEA28V1 trades refresh error:",
                error
            );
        }

    },
    60000
);
javascript
"use strict";

/*
 * ============================================================
 * TRADES PAGE
 * ============================================================
 *
 * PUBLIC DATA STRUCTURE
 *
 * data/
 *   analysis/
 *     index.json
 *
 *     TICKER/
 *       trades.json
 *
 * ============================================================
 *
 * DATE SELECTOR BEHAVIOR
 *
 * "" / "All Dates"
 *     -> show all trades
 *
 * "YYYY-MM-DD"
 *     -> show trades whose ACTUAL trade date matches
 *        the selected date
 *
 * ?ticker=AAPL
 *     + All Dates
 *     -> all AAPL trades
 *
 * ?ticker=AAPL
 *     + specific date
 *     -> AAPL trades for that date
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
   GENERIC JSON LOADER
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
   DATE HELPERS
   ============================================================ */

function isValidDateString(value) {

    return (
        typeof value === "string" &&
        /^\d{4}-\d{2}-\d{2}$/.test(
            value
        )
    );
}

function formatDateLabel(date) {

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
   TRADE DATE
   ============================================================ */

function getTradeDate(trade) {

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
     * Preserve an explicit YYYY-MM-DD prefix.
     */
    const directMatch =
        text.match(
            /^(\d{4}-\d{2}-\d{2})/
        );

    if (directMatch) {
        return directMatch[1];
    }

    /*
     * Handle other valid JavaScript date values.
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
   TRADE TIMESTAMP
   ============================================================ */

function getTradeTimestamp(trade) {

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
   GET AVAILABLE DATES
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
   CREATE / FIND DATE SELECTOR
   ============================================================ */

function findDateSelector() {

    const existing =
        document.getElementById(
            "tradeDate"
        );

    if (existing) {
        return existing;
    }

    /*
     * trades.html uses:
     *
     * <div class="trade-controls">
     *
     * Insert the selector there.
     */
    const container =
        document.querySelector(
            ".trade-controls"
        );

    if (!container) {

        console.error(
            "Unable to create trade date selector: .trade-controls was not found."
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

    /*
     * Use the existing trade-controls layout.
     */
    wrapper.style.display =
        "flex";

    wrapper.style.alignItems =
        "center";

    wrapper.style.gap =
        "10px";

    const label =
        document.createElement(
            "label"
        );

    label.htmlFor =
        "tradeDate";

    label.textContent =
        "Trade Date";

    label.style.color =
        "var(--muted)";

    label.style.fontSize =
        "11px";

    label.style.fontWeight =
        "800";

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

/* ============================================================
   INITIALIZE DATE SELECTOR
   ============================================================ */

function initializeDateSelector(
    dates,
    preserveSelectedDate = false
) {

    const selector =
        findDateSelector();

    if (!selector) {
        return null;
    }

    /*
     * Preserve the user's current selection during
     * auto-refresh when possible.
     */
    const currentSelection =
        selectedDate;

    selector.innerHTML =
        "";

    /*
     * ========================================================
     * ALL DATES OPTION
     * ========================================================
     *
     * This is intentionally value="".
     *
     * It means:
     *
     *     do not apply a date filter
     *
     * ========================================================
     */

    const allDatesOption =
        document.createElement(
            "option"
        );

    allDatesOption.value =
        "";

    allDatesOption.textContent =
        "All Dates";

    selector.appendChild(
        allDatesOption
    );

    /*
     * If there are no published dates,
     * All Dates remains available but disabled.
     */
    if (!dates.length) {

        selector.disabled =
            true;

        selectedDate =
            "";

        allDatesOption.selected =
            true;

        updateUrlDate(
            ""
        );

        return selector;
    }

    selector.disabled =
        false;

    const requestedDate =
        getRequestedDate();

    /*
     * Determine which date should be selected.
     *
     * Priority:
     *
     * 1. Existing user selection during refresh
     * 2. Valid ?date= URL parameter
     * 3. All Dates
     *
     * IMPORTANT:
     *
     * The default is now ALL DATES.
     */
    if (
        preserveSelectedDate &&
        (
            currentSelection === "" ||
            dates.includes(
                currentSelection
            )
        )
    ) {

        selectedDate =
            currentSelection;

    } else if (
        requestedDate &&
        dates.includes(
            requestedDate
        )
    ) {

        selectedDate =
            requestedDate;

    } else {

        selectedDate =
            "";
    }

    /*
     * Add each published date.
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
     * Explicitly select All Dates when selectedDate
     * is empty.
     */
    if (
        selectedDate === ""
    ) {
        selector.value =
            "";
    }

    /*
     * Attach the change handler exactly once.
     */
    if (
        !dateSelectorInitialized
    ) {

        selector.addEventListener(
            "change",
            async () => {

                const date =
                    selector.value;

                /*
                 * Empty string is VALID here.
                 *
                 * It means:
                 *
                 *     ALL DATES
                 */
                if (
                    date !== "" &&
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

                try {

                    await loadTradesForDate(
                        date,
                        getRequestedTicker()
                    );

                } catch (error) {

                    console.error(
                        "Failed to load selected trade date:",
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

    /*
     * Keep the URL synchronized.
     *
     * For All Dates, remove ?date entirely.
     */
    updateUrlDate(
        selectedDate
    );

    return selector;
}

/* ============================================================
   UPDATE URL
   ============================================================ */

function updateUrlDate(date) {

    const url =
        new URL(
            window.location.href
        );

    if (
        date === ""
    ) {

        /*
         * All Dates does not need a date parameter.
         */
        url.searchParams.delete(
            "date"
        );

    } else if (
        isValidDateString(
            date
        )
    ) {

        url.searchParams.set(
            "date",
            date
        );

    } else {

        return;
    }

    window.history.replaceState(
        {},
        "",
        url
    );
}

/* ============================================================
   LOAD TRADES FOR SELECTED DATE
   ============================================================ */

async function loadTradesForDate(
    date,
    requestedTicker = null
) {

    allTrades =
        [];

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

    /*
     * If a ticker is supplied, restrict the page
     * to that ticker.
     *
     * Otherwise load every ticker.
     */
    const tickersToLoad =
        requestedTicker
            ? tickerNames.filter(
                ticker =>
                    ticker.toUpperCase() ===
                    requestedTicker
            )
            : tickerNames;

    const loadedTrades =
        [];

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
         * ====================================================
         * DATE PUBLICATION FILTER
         * ====================================================
         *
         * When a specific date is selected, the ticker
         * must be published for that date.
         *
         * When date === "":
         *
         *     DO NOT apply this filter.
         *
         * That is what makes "All Dates" work.
         * ====================================================
         */

        if (
            date !== "" &&
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
             * =================================================
             * ACTUAL TRADE DATE FILTER
             * =================================================
             *
             * Specific date:
             *
             *     actual trade date === selected date
             *
             * All Dates:
             *
             *     no date filter
             * =================================================
             */

            let matchingTrades;

            if (
                date === ""
            ) {

                matchingTrades =
                    trades.slice();

            } else {

                matchingTrades =
                    trades.filter(
                        trade =>
                            getTradeDate(
                                trade
                            ) === date
                    );
            }

            if (
                !matchingTrades.length
            ) {
                continue;
            }

            /*
             * =================================================
             * IMPORTANT
             * =================================================
             *
             * For a SPECIFIC date:
             *
             *     keep only the latest trade for that
             *     ticker/date.
             *
             * For ALL DATES:
             *
             *     keep ALL historical trade records.
             *
             * This is necessary because "All Dates" means
             * the complete trade history, not just the newest
             * record.
             * =================================================
             */

            if (
                date === ""
            ) {

                matchingTrades.sort(
                    (a, b) =>
                        getTradeTimestamp(b) -
                        getTradeTimestamp(a)
                );

                matchingTrades.forEach(
                    trade => {

                        loadedTrades.push({
                            ...trade,

                            _ticker:
                                ticker,

                            _date:
                                getTradeDate(
                                    trade
                                )
                        });
                    }
                );

            } else {

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
            }

        } catch (error) {

            console.error(
                `Failed to load trades for ${ticker}:`,
                error
            );
        }
    }

    allTrades =
        loadedTrades;

    renderTrades();
}

/* ============================================================
   INITIALIZE TRADES PAGE
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
            getAvailableDates(
                index
            );

        /*
         * Build the selector.
         *
         * The default is ALL DATES unless ?date=YYYY-MM-DD
         * was explicitly supplied.
         */
        const selector =
            initializeDateSelector(
                availableDates
            );

        if (
            !availableDates.length
        ) {

            /*
             * There are no published dates at all.
             */
            renderDataUnavailable(
                "No published trade dates are available."
            );

            return;
        }

        if (
            selector
        ) {

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
            "Failed to initialize trade data:",
            error
        );

        renderDataUnavailable(
            "Unable to load trade history."
        );
    }
}

/* ============================================================
   RENDER TRADES
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

            let comparison =
                0;

            if (
                typeof aValue ===
                    "number" &&
                typeof bValue ===
                    "number"
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
                            numeric:
                                true,
                            sensitivity:
                                "base"
                        }
                    );
            }

            return (
                sortDirection ===
                "asc"
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

            /*
             * Single-click navigation.
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
                     * When viewing All Dates, use the
                     * actual trade date for the profile.
                     *
                     * When viewing a specific date,
                     * selectedDate is already the correct
                     * date.
                     */
                    const date =
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
                            date
                        )
                    ) {
                        url +=
                            `&date=${encodeURIComponent(
                                date
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
   DISPLAY SELECTED DATE
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
        selectedDate === ""
    ) {

        updated.textContent =
            "All Dates";

        return;
    }

    if (
        !selectedDate
    ) {
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
                        sortDirection ===
                            "asc"
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
                    tickerSearch.value =
                        "";
                }

                if (directionFilter) {
                    directionFilter.value =
                        "";
                }

                if (statusFilter) {
                    statusFilter.value =
                        "";
                }

                renderTrades();
            }
        );
    }
}

/* ============================================================
   ERROR DISPLAY
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

    return Number.isFinite(
        number
    )
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

    if (
        !Number.isFinite(
            number
        )
    ) {
        return "—";
    }

    return number < 1
        ? "$" +
            number.toFixed(4)
        : "$" +
            number.toFixed(2);
}

function escapeHtml(value) {

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
   AUTO REFRESH
   ============================================================ */

setInterval(
    async () => {

        try {

            const index =
                await getJSON(
                    ANALYSIS_INDEX_PATH
                );

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

                const previousDate =
                    selectedDate;

                availableDates =
                    newDates;

                /*
                 * Rebuild selector while preserving
                 * All Dates or the user's selected date.
                 */
                initializeDateSelector(
                    availableDates,
                    true
                );

                selectedDate =
                    previousDate;

                const selector =
                    document.getElementById(
                        "tradeDate"
                    );

                if (selector) {

                    selector.value =
                        previousDate;
                }
            }

            /*
             * Reload using the current selection.
             *
             * "" means ALL DATES.
             */
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


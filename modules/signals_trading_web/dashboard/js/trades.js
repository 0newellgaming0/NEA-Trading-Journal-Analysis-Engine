"use strict";

/* ============================================================
NEA28V1 TRADES PAGE
===================

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

IMPORTANT:

The ticker directory in index.json is authoritative.

The loader:
1. Reads data/analysis/index.json
2. Determines the selected publication date
3. Loads only ticker directories published on that date
4. Loads that ticker's trades.json
5. Normalizes records using the newsletter contract
6. Inherits ticker from the directory when necessary
7. Requires actual trade date == selected date
8. Keeps the latest trade for ticker/date
9. Sends the resulting records to #trades

There is NO "All Dates" default.
============================================================ */

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
    ).padStart(
        2,
        "0"
    ),
    String(
        now.getDate()
    ).padStart(
        2,
        "0"
    )
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

/*

* The actual trade/publication record remains authoritative.
*
* We intentionally check the same fields used by newsletter.js,
* with a few additional aliases used by the publication system.
  */
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

  
       raw.trade_date_key,
       raw.tradeDateKey,

       raw.publication_date,
       raw.publicationDate,

       raw.analysis_date,
       raw.analysisDate,

       raw.date,

       raw.created_date,
       raw.createdDate,

       raw.created_at,
       raw.createdAt,

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

  * Preserve explicit YYYY-MM-DD prefixes.
  *
  * Example:
  * 2026-09-01
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

        raw.created_at,
        raw.createdAt,

        raw.updated_at,
        raw.updatedAt,

        raw.generated_at,
        raw.generatedAt
    );

if (!timestamp) {
    return 0;
}

/*
 * Handle explicit ISO timestamps as well as
 * ordinary JavaScript date values.
 */
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

/*

* This mirrors newsletter.js but is deliberately slightly
* more tolerant of the publication files.
*
* Supported:
*
* []
*
* { trades: [] }
*
* { data: [] }
*
* { trade: {...} }
*
* a single trade object
  */
  function normalizeTradeData(
  data,
  fallbackTicker = null
  ) {


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

} else if (
    data &&
    data.trade &&
    typeof data.trade === "object"
) {

    source = [
        data.trade
    ];

} else if (
    data &&
    typeof data === "object"
) {

    /*
     * Some publication files contain one trade object
     * directly rather than wrapping it in {trades: []}.
     */
    source = [
        data
    ];

} else {

    source = [];
}

return source
    .map(
        trade =>
            normalizeTrade(
                trade,
                fallbackTicker
            )
    )
    .filter(Boolean);


}

/*

* IMPORTANT FIX:
*
* ticker is allowed to come from the authoritative
* ticker directory.
*
* Therefore:
*
* data/analysis/LVLU/trades.json
*
* is sufficient to identify LVLU even if the individual
* record does not contain:
*
* "ticker": "LVLU"
  */
  function normalizeTrade(
  trade,
  fallbackTicker = null
  ) {

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
  trade.Symbol,
  fallbackTicker
  );

  if (!ticker) {
  return null;
  }

  const entry =
  numericValue(
  firstValue(
  trade.entry,
  trade.entry_price,
  trade.entryPrice,
  trade.Entry
  )
  );

  const stop =
  numericValue(
  firstValue(
  trade.stop,
  trade.stop_loss,
  trade.stopLoss,
  trade.Stop
  )
  );

  const target =
  numericValue(
  firstValue(
  trade.target,
  trade.target_price,
  trade.targetPrice,
  trade.Target
  )
  );

  const score =
  numericValue(
  firstValue(
  trade.score,
  trade.rank_score,
  trade.rankScore,
  trade.Score
  )
  );

  const currentPrice =
  numericValue(
  firstValue(
  trade.current_price,
  trade.currentPrice,
  trade.current,
  trade.price,
  trade.Price
  )
  );

  return {

  
   ticker:
       String(
           ticker
       )
       .trim()
       .toUpperCase(),

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
           trade.setupType,
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
       currentPrice,

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
 * Determines the initially selected date.
 *
 * IMPORTANT:
 *
 * "All Dates" remains an available selector option.
 *
 * The DEFAULT is:
 *
 * 1. Existing selection during refresh
 * 2. Explicit ?date=YYYY-MM-DD
 * 3. TODAY, if published
 * 4. Latest published date
 *
 * All Dates is NOT the default.
 */
function determineInitialDate(
    dates,
    preserveSelection = false
) {

    const requestedDate =
        getRequestedDate();

    const today =
        getTodayDateKey();

    /*
     * Preserve the user's current selection during
     * auto-refresh, INCLUDING All Dates ("").
     */
    if (
        preserveSelection
    ) {

        if (
            selectedDate === "" ||
            dates.includes(
                selectedDate
            )
        ) {
            return selectedDate;
        }
    }

    /*
     * Explicit URL date takes priority.
     */
    if (
        requestedDate &&
        dates.includes(
            requestedDate
        )
    ) {
        return requestedDate;
    }

    /*
     * TODAY is the default.
     */
    if (
        dates.includes(
            today
        )
    ) {
        return today;
    }

    /*
     * If today has not been published yet,
     * use the newest published date.
     *
     * This does NOT mean All Dates.
     */
    if (dates.length) {
        return dates[0];
    }

    return "";
}


/* ============================================================
   DATE SELECTOR
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

    selector.innerHTML =
        "";

    /*
     * ========================================================
     * ALL DATES MUST REMAIN AVAILABLE
     * ========================================================
     *
     * Empty string is the internal value representing
     * All Dates.
     */
    const allOption =
        document.createElement(
            "option"
        );

    allOption.value =
        "";

    allOption.textContent =
        "All Dates";

    selector.appendChild(
        allOption
    );

    /*
     * No published dates at all.
     */
    if (
        !Array.isArray(dates) ||
        !dates.length
    ) {

        selector.disabled =
            false;

        selectedDate =
            "";

        selector.value =
            "";

        updateUrlDate(
            ""
        );

        return selector;
    }

    selector.disabled =
        false;

    /*
     * Add every published date.
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

    /*
     * Determine the actual initial selection.
     *
     * This returns TODAY when available,
     * NOT All Dates.
     */
    selectedDate =
        determineInitialDate(
            dates,
            preserveSelection
        );

    selector.value =
        selectedDate;

    /*
     * Install the change handler only once.
     */
    if (
        !dateSelectorInitialized
    ) {

        selector.addEventListener(
            "change",
            async () => {

                selectedDate =
                    selector.value;

                /*
                 * Empty string means All Dates.
                 *
                 * Therefore the URL date parameter
                 * is removed when All Dates is selected.
                 */
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
     * Empty date string means:
     *
     * ALL DATES
     *
     * A specific YYYY-MM-DD means:
     *
     * ONLY THAT DATE
     */
    const isAllDates =
        date === "";

    if (
        !isAllDates &&
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
                    String(ticker)
                        .trim()
                        .toUpperCase() ===
                    requestedTicker
            )
            : tickerEntries;

    const loadedTrades =
        [];

    console.log(
        `NEA28V1 trades: loading ${
            isAllDates
                ? "ALL DATES"
                : date
        }`
    );

    console.log(
        `NEA28V1 trades: candidate tickers ${entriesToLoad.length}`
    );

    /*
     * ========================================================
     * LOAD EACH AUTHORITATIVE TICKER DIRECTORY
     * ========================================================
     */

    for (
        const [
            ticker,
            publishedDates
        ]
        of entriesToLoad
    ) {

        const normalizedTicker =
            String(
                ticker
            )
            .trim()
            .toUpperCase();

        if (
            !Array.isArray(
                publishedDates
            )
        ) {
            continue;
        }

        /*
         * ====================================================
         * PUBLICATION GATE
         * ====================================================
         *
         * Specific date:
         *
         *     ticker must be published on that date.
         *
         * All Dates:
         *
         *     ticker is eligible if it has at least one
         *     published date.
         */

        if (
            !publishedDates.length
        ) {
            continue;
        }

        if (
            !isAllDates &&
            !publishedDates.includes(
                date
            )
        ) {
            continue;
        }

        const tradeFile =
            `data/analysis/${encodeURIComponent(
                normalizedTicker
            )}/trades.json`;

        try {

            console.log(
                `NEA28V1 trades: loading ${tradeFile}`
            );

            const data =
                await getJSON(
                    tradeFile
                );

            /*
             * The ticker directory is authoritative.
             *
             * Therefore the ticker is supplied as a
             * fallback if the trade record itself does
             * not contain one.
             */
            const trades =
                normalizeTradeData(
                    data,
                    normalizedTicker
                );

            console.log(
                `NEA28V1 trades: ${normalizedTicker} normalized ${trades.length} record(s)`
            );

            if (
                !trades.length
            ) {
                continue;
            }

            /*
             * =================================================
             * DATE FILTER
             * =================================================
             *
             * Specific date:
             *
             *     require actual trade date === selected date.
             *
             * All Dates:
             *
             *     allow every valid trade date contained in
             *     trades.json.
             */
            const matchingTrades =
                trades.filter(
                    trade => {

                        const tradeDate =
                            getTradeDate(
                                trade
                            );

                        /*
                         * Every displayed trade must have
                         * an identifiable date.
                         */
                        if (
                            !isValidDateString(
                                tradeDate
                            )
                        ) {
                            return false;
                        }

                        if (
                            isAllDates
                        ) {
                            return true;
                        }

                        return (
                            tradeDate ===
                            date
                        );
                    }
                );

            console.log(
                `NEA28V1 trades: ${normalizedTicker} has ${matchingTrades.length} trade(s) matching ${
                    isAllDates
                        ? "ALL DATES"
                        : date
                }`
            );

            if (
                !matchingTrades.length
            ) {
                continue;
            }

            /*
             * =================================================
             * SORT NEWEST FIRST
             * =================================================
             */
            matchingTrades.sort(
                (a, b) => {

                    const timestampDifference =
                        getTradeTimestamp(b) -
                        getTradeTimestamp(a);

                    /*
                     * If timestamps are identical or unavailable,
                     * fall back to the trade date.
                     */
                    if (
                        timestampDifference !== 0
                    ) {
                        return timestampDifference;
                    }

                    return (
                        getTradeDate(b) || ""
                    ).localeCompare(
                        getTradeDate(a) || ""
                    );
                }
            );

            /*
             * =================================================
             * KEEP LATEST RECORD
             * =================================================
             *
             * For a specific date:
             *
             *     one latest trade per ticker/date.
             *
             * For All Dates:
             *
             *     one latest trade per ticker.
             *
             * This prevents duplicate historical records
             * for the same ticker from filling the table.
             */
            const latest =
                matchingTrades[0];

            const latestDate =
                getTradeDate(
                    latest
                );

            loadedTrades.push({

                ...latest,

                _ticker:
                    normalizedTicker,

                _date:
                    latestDate,

                _analysisDate:
                    latestDate
            });

        } catch (error) {

            console.warn(
                `Unable to load trades for ${normalizedTicker}:`,
                error
            );
        }
    }

    /*
     * ========================================================
     * AUTHORITATIVE TABLE DATASET
     * ========================================================
     */

    allTrades =
        loadedTrades;

    console.log(
        `NEA28V1 trades: ${allTrades.length} trade(s) loaded for ${
            isAllDates
                ? "ALL DATES"
                : date
        }`
    );

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

    const selector =
        initializeDateSelector(
            availableDates
        );

    if (selector) {

        selectedDate =
            selector.value;
    }

    /*
     * IMPORTANT:
     *
     * Load the selected date immediately.
     */
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
         * Continue using the currently selected date.
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

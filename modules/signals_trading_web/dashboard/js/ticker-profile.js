"use strict";

document.addEventListener(
"DOMContentLoaded",
initializeTickerProfile
);

let tickerTradeRecords = [];
let currentTradeRecord = null;
let requestedTicker = null;
let tickerAnalysisData = null;

async function initializeTickerProfile() {


showLoading();

requestedTicker =
    getRequestedTicker();

if (!requestedTicker) {

    showError(
        "No ticker was specified. Open a ticker profile from a published trade opportunity."
    );

    return;
}

try {

    const data =
        await loadTickerTradeData(
            requestedTicker
        );

    tickerTradeRecords =
        normalizeTradeData(
            data
        );

    if (!tickerTradeRecords.length) {

        showError(
            `No published NEA28V1 trade data was found for ${requestedTicker}.`
        );

        return;
    }

    currentTradeRecord =
        findCurrentTickerTrade(
            tickerTradeRecords,
            requestedTicker
        );

    if (!currentTradeRecord) {

        showError(
            `No current NEA28V1 trade data was found for ${requestedTicker}.`
        );

        return;
    }

    tickerAnalysisData =
        await loadTickerAnalysisData(
            requestedTicker
        );

    initializeAnalysisDateSelector();

    renderTickerProfile(
        currentTradeRecord
    );

    renderAnalysisBlocks(
        tickerAnalysisData
    );

    bindAnalysisDateSelector();

} catch (error) {

    console.error(
        "NEA28V1 ticker profile error:",
        error
    );

    showError(
        `Unable to load the published trade data for ${requestedTicker}.`
    );
}


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

const normalized =
    ticker
        .trim()
        .toUpperCase();

return normalized || null;


}

async function loadTickerTradeData(
ticker
) {


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


}

async function loadTickerAnalysisData(
ticker
) {


const url =
    `data/analysis/${encodeURIComponent(
        ticker
    )}/${encodeURIComponent(
        ticker
    )}_analysis_latest.json?t=${Date.now()}`;

const response =
    await fetch(
        url,
        {
            cache: "no-store"
        }
    );

if (!response.ok) {

    console.warn(
        `NEA28V1 ticker profile: analysis data unavailable for ${ticker}: ${response.status}`
    );

    return null;
}

const data =
    await response.json();

if (
    !data ||
    typeof data !== "object"
) {
    return null;
}

return data;


}

function normalizeTradeData(data) {


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


}

function normalizeTrade(trade) {


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
        trade.updated_at,

    analysisDate:
        normalizeTradeDate(
            trade.analysis_date ||
            trade.trade_date ||
            trade.date ||
            trade.created_at ||
            trade.updated_at
        ),

    raw:
        trade
};


}

function findCurrentTickerTrade(
trades,
ticker
) {


const tickerTrades =
    trades.filter(
        trade =>
            trade.ticker === ticker
    );

if (!tickerTrades.length) {
    return null;
}

const today =
    getCurrentDateKey();

const todayTrade =
    tickerTrades.find(
        trade =>
            trade.analysisDate === today
    );

if (todayTrade) {
    return todayTrade;
}

return tickerTrades
    .slice()
    .sort(
        (a, b) =>
            getTradeTimestamp(b) -
            getTradeTimestamp(a)
    )[0];


}

function findTickerTradeByDate(
trades,
ticker,
date
) {


return trades.find(
    trade =>
        trade.ticker === ticker &&
        trade.analysisDate === date
) || null;


}

function getTradeTimestamp(
trade
) {


const value =
    trade.updatedAt ||
    trade.createdAt ||
    trade.analysisDate;

const date =
    parseTimestamp(
        value
    );

if (!date) {
    return 0;
}

return date.getTime();


}

function normalizeTradeDate(
value
) {


if (
    value === null ||
    value === undefined ||
    value === ""
) {
    return null;
}

const raw =
    String(value).trim();

const match =
    raw.match(
        /^(\d{4}-\d{2}-\d{2})/
    );

if (match) {
    return match[1];
}

const date =
    parseTimestamp(
        raw
    );

if (!date) {
    return null;
}

return [
    date.getFullYear(),
    String(
        date.getMonth() + 1
    ).padStart(2, "0"),
    String(
        date.getDate()
    ).padStart(2, "0")
].join("-");


}

function getCurrentDateKey() {


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

function initializeAnalysisDateSelector() {


const selector =
    document.getElementById(
        "analysisDate"
    );

if (!selector) {
    return;
}

selector.innerHTML = "";

const tickerTrades =
    tickerTradeRecords
        .filter(
            trade =>
                trade.ticker === requestedTicker &&
                trade.analysisDate
        )
        .sort(
            (a, b) =>
                b.analysisDate.localeCompare(
                    a.analysisDate
                )
        );

const uniqueDates =
    [
        ...new Set(
            tickerTrades.map(
                trade =>
                    trade.analysisDate
            )
        )
    ];

const today =
    getCurrentDateKey();

if (
    !uniqueDates.includes(today) &&
    currentTradeRecord.analysisDate
) {

    uniqueDates.unshift(
        currentTradeRecord.analysisDate
    );
}

uniqueDates.forEach(
    date => {

        const option =
            document.createElement(
                "option"
            );

        option.value =
            date;

        option.textContent =
            formatAnalysisDate(
                date
            );

        if (
            date === currentTradeRecord.analysisDate
        ) {

            option.selected =
                true;
        }

        selector.appendChild(
            option
        );
    }
);

if (!selector.value) {

    selector.value =
        currentTradeRecord.analysisDate ||
        today;
}


}

function bindAnalysisDateSelector() {


const selector =
    document.getElementById(
        "analysisDate"
    );

if (!selector) {
    return;
}

selector.addEventListener(
    "change",
    handleAnalysisDateChange
);


}

function handleAnalysisDateChange(
event
) {


const selectedDate =
    event.target.value;

const currentDate =
    getCurrentDateKey();

if (
    !selectedDate ||
    selectedDate === currentDate
) {

    renderTickerProfile(
        currentTradeRecord
    );

    renderAnalysisBlocks(
        tickerAnalysisData
    );

    return;
}

const historicalTrade =
    findTickerTradeByDate(
        tickerTradeRecords,
        requestedTicker,
        selectedDate
    );

if (!historicalTrade) {

    renderHistoricalTradeUnavailable(
        selectedDate
    );

    return;
}

renderTickerProfile(
    currentTradeRecord
);

renderAnalysisBlocks(
    tickerAnalysisData
);

renderHistoricalTradeSetup(
    historicalTrade
);


}

function renderTickerProfile(
trade
) {


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
    "analysisGeneratedAt",
    formatTimestamp(
        tickerAnalysisData?.generated_at ||
        trade.updatedAt ||
        trade.createdAt
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

removeHistoricalTradeSetup();

hideLoading();
hideError();
showProfile();


}

function renderAnalysisBlocks(
data
) {


const section =
    document.getElementById(
        "analysisSection"
    );

if (!section) {
    return;
}

const existingBlocks =
    section.querySelector(
        ".analysis-blocks"
    );

if (existingBlocks) {
    existingBlocks.remove();
}

if (
    !data ||
    !data.tickers ||
    typeof data.tickers !== "object"
) {
    return;
}

const tickerData =
    data.tickers[
        requestedTicker
    ];

if (
    !tickerData ||
    typeof tickerData !== "object"
) {
    return;
}

const blocks =
    tickerData.analysis_blocks;

if (
    !blocks ||
    typeof blocks !== "object"
) {
    return;
}

const entries =
    Object.entries(
        blocks
    ).filter(
        ([, value]) =>
            value !== null &&
            value !== undefined &&
            value !== ""
    );

if (!entries.length) {
    return;
}

const container =
    document.createElement(
        "div"
    );

container.className =
    "analysis-blocks";

entries.forEach(
    ([title, content], index) => {

        const card =
            document.createElement(
                "article"
            );

        card.className =
            "analysis-card";

        card.innerHTML =
            `
            <button
                type="button"
                class="analysis-card-header"
                aria-expanded="true">

                <span class="analysis-card-index">
                    ${index + 1}
                </span>

                <h3>
                    ${escapeHTML(
                        formatAnalysisTitle(
                            title
                        )
                    )}
                </h3>

            </button>

            <div class="analysis-card-content">
                ${renderAnalysisContent(
                    content
                )}
            </div>
            `;

        const header =
            card.querySelector(
                ".analysis-card-header"
            );

        header.addEventListener(
            "click",
            () =>
                toggleAnalysisCard(
                    card
                )
        );

        container.appendChild(
            card
        );
    }
);

section.appendChild(
    container
);


}

function formatAnalysisTitle(
value
) {


return String(value)
    .replace(
        /[_-]+/g,
        " "
    )
    .replace(
        /\s+/g,
        " "
    )
    .trim()
    .replace(
        /\b\w/g,
        character =>
            character.toUpperCase()
    );


}

function renderAnalysisContent(
content
) {


if (
    content === null ||
    content === undefined
) {
    return "";
}

if (
    typeof content === "string"
) {
    return renderAnalysisText(
        content
    );
}

if (Array.isArray(content)) {

    return `
        <div class="analysis-list">
            ${content
                .map(
                    item =>
                        `
                        <div class="analysis-list-item">
                            ${renderAnalysisContent(
                                item
                            )}
                        </div>
                        `
                )
                .join("")
            }
        </div>
    `;
}

if (
    typeof content === "object"
) {

    return `
        <div class="analysis-data">
            ${Object.entries(
                content
            )
                .map(
                    ([key, value]) =>
                        `
                        <div class="analysis-data-item">
                            <span>
                                ${escapeHTML(
                                    formatAnalysisTitle(
                                        key
                                    )
                                )}
                            </span>

                            <strong>
                                ${renderAnalysisValue(
                                    value
                                )}
                            </strong>
                        </div>
                        `
                )
                .join("")
            }
        </div>
    `;
}

return `
    <p>
        ${escapeHTML(
            String(content)
        )}
    </p>
`;


}

function renderAnalysisText(
value
) {


const text =
    String(value);

const lines =
    text.split(/\r?\n/);

return lines
    .map(
        line => {

            const trimmed =
                line.trim();

            if (!trimmed) {
                return "";
            }

            if (
                /^#{1,6}\s+/.test(
                    trimmed
                )
            ) {

                const heading =
                    trimmed.replace(
                        /^#{1,6}\s+/,
                        ""
                    );

                return `
                    <h4>
                        ${escapeHTML(
                            heading
                        )}
                    </h4>
                `;
            }

            return `
                <p>
                    ${escapeHTML(
                        trimmed
                    )}
                </p>
            `;
        }
    )
    .join("");


}

function renderAnalysisValue(
value
) {


if (
    value === null ||
    value === undefined
) {
    return "—";
}

if (
    typeof value === "object"
) {

    return escapeHTML(
        JSON.stringify(
            value,
            null,
            2
        )
    );
}

return escapeHTML(
    String(value)
);


}

function toggleAnalysisCard(
card
) {


const header =
    card.querySelector(
        ".analysis-card-header"
    );

if (!header) {
    return;
}

const expanded =
    header.getAttribute(
        "aria-expanded"
    ) === "true";

header.setAttribute(
    "aria-expanded",
    String(!expanded)
);

card.classList.toggle(
    "is-expanded",
    !expanded
);


}

function renderHistoricalTradeSetup(
trade
) {


removeHistoricalTradeSetup();

const anchor =
    document.getElementById(
        "analysisSection"
    );

if (!anchor) {
    return;
}

const card =
    document.createElement(
        "article"
    );

card.id =
    "historicalTradeSetup";

card.className =
    "analysis-card historical-trade-setup";

card.innerHTML =
    buildHistoricalTradeSetupHTML(
        trade
    );

anchor.parentNode.insertBefore(
    card,
    anchor
);

card
    .querySelector(
        ".analysis-card-header"
    )
    ?.addEventListener(
        "click",
        () =>
            toggleHistoricalTradeCard(
                card
            )
    );


}

function buildHistoricalTradeSetupHTML(
trade
) {


const values = [

    [
        "ANALYSIS DATE",
        formatAnalysisDate(
            trade.analysisDate
        )
    ],

    [
        "TICKER",
        trade.ticker
    ],

    [
        "DIRECTION",
        trade.direction
    ],

    [
        "SETUP",
        trade.setup
    ],

    [
        "REGIME",
        trade.regime
    ],

    [
        "TIMEFRAME",
        trade.timeframe
    ],

    [
        "CURRENT PRICE",
        formatPrice(
            trade.currentPrice
        )
    ],

    [
        "ENTRY",
        formatPrice(
            trade.entry
        )
    ],

    [
        "STOP",
        formatPrice(
            trade.stop
        )
    ],

    [
        "TARGET",
        formatPrice(
            trade.target
        )
    ],

    [
        "RISK / REWARD",
        formatRiskReward(
            trade.riskReward
        )
    ],

    [
        "SCORE",
        formatScore(
            trade.score
        )
    ],

    [
        "STATUS",
        trade.status
    ],

    [
        "SIGNAL STRENGTH",
        trade.signalStrength
    ],

    [
        "CONFLUENCE",
        formatConfluence(
            trade.confluence
        )
    ],

    [
        "CREATED",
        formatTimestamp(
            trade.createdAt
        )
    ],

    [
        "UPDATED",
        formatTimestamp(
            trade.updatedAt
        )
    ]
];

const dataHTML =
    values
        .map(
            ([label, value]) =>
                `
                <div class="analysis-data-item">
                    <span>${escapeHTML(label)}</span>
                    <strong>${escapeHTML(value)}</strong>
                </div>
                `
        )
        .join("");

return `
    <button
        type="button"
        class="analysis-card-header"
        aria-expanded="true">

        <span class="analysis-card-index">
            HIST
        </span>

        <h3>
            ${escapeHTML(
                trade.ticker
            )} — Trade Setup —
            ${escapeHTML(
                formatAnalysisDate(
                    trade.analysisDate
                )
            )}
        </h3>

    </button>

    <div class="analysis-card-content">

        <div class="analysis-data">
            ${dataHTML}
        </div>

    </div>
`;


}

function toggleHistoricalTradeCard(
card
) {


const header =
    card.querySelector(
        ".analysis-card-header"
    );

const expanded =
    header.getAttribute(
        "aria-expanded"
    ) === "true";

header.setAttribute(
    "aria-expanded",
    String(!expanded)
);

card.classList.toggle(
    "is-expanded",
    !expanded
);


}

function renderHistoricalTradeUnavailable(
date
) {


removeHistoricalTradeSetup();

const anchor =
    document.getElementById(
        "analysisSection"
    );

if (!anchor) {
    return;
}

const card =
    document.createElement(
        "article"
    );

card.id =
    "historicalTradeSetup";

card.className =
    "analysis-card analysis-diagnostic historical-trade-setup";

card.innerHTML = `
    <div class="analysis-card-header">
        <span class="analysis-card-index">
            HIST
        </span>

        <h3>
            No Trade Setup Published
        </h3>
    </div>

    <div class="analysis-card-content">
        <p>
            No NEA28V1 trade setup was published
            for ${escapeHTML(
                formatAnalysisDate(date)
            )}.
        </p>
    </div>
`;

anchor.parentNode.insertBefore(
    card,
    anchor
);


}

function removeHistoricalTradeSetup() {


const existing =
    document.getElementById(
        "historicalTradeSetup"
    );

if (existing) {
    existing.remove();
}


}

function formatAnalysisDate(
value
) {


if (!value) {
    return "—";
}

const parts =
    String(value).split("-");

if (
    parts.length !== 3
) {
    return String(value);
}

const date =
    new Date(
        Number(parts[0]),
        Number(parts[1]) - 1,
        Number(parts[2])
    );

if (
    Number.isNaN(
        date.getTime()
    )
) {
    return String(value);
}

return date.toLocaleDateString(
    "en-US",
    {
        month: "short",
        day: "numeric",
        year: "numeric"
    }
);


}

function parseTimestamp(
value
) {


if (
    value === null ||
    value === undefined ||
    value === ""
) {
    return null;
}

let raw =
    String(value).trim();

if (!raw) {
    return null;
}

/*
 * Publication timestamps are UTC.
 * Explicit UTC/offset timestamps are
 * preserved exactly as supplied.
 *
 * A timestamp without a timezone is
 * treated as UTC rather than allowing
 * the browser to interpret it as local.
 */
if (
    !/[zZ]|[+-]\d{2}:?\d{2}$/.test(
        raw
    )
) {

    raw =
        raw.replace(
            " ",
            "T"
        ) + "Z";
}

const date =
    new Date(raw);

if (
    Number.isNaN(
        date.getTime()
    )
) {
    return null;
}

return date;


}

function formatTimestamp(
value
) {


const date =
    parseTimestamp(
        value
    );

if (!date) {
    return "—";
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


}

function buildOpportunityDescription(
trade
) {


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


}

function numericValue(
value
) {


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


}

function displayValue(
value
) {


if (
    value === null ||
    value === undefined ||
    value === ""
) {
    return "—";
}

return String(value);


}

function formatPrice(
value
) {


if (!Number.isFinite(value)) {
    return "—";
}

return `$${value.toFixed(4)}`;


}

function formatRiskReward(
value
) {


if (!Number.isFinite(value)) {
    return "—";
}

return `${value.toFixed(2)}R`;


}

function formatScore(
value
) {


if (!Number.isFinite(value)) {
    return "—";
}

return Number.isInteger(value)
    ? String(value)
    : value.toFixed(2);


}

function formatConfluence(
value
) {


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


}

function escapeHTML(
value
) {


return String(
    value ?? "—"
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

function setText(
id,
value
) {


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


}

function showLoading() {


const element =
    document.getElementById(
        "loadingState"
    );

if (element) {

    element.classList.remove(
        "hidden"
    );
}


}

function hideLoading() {


const element =
    document.getElementById(
        "loadingState"
    );

if (element) {

    element.classList.add(
        "hidden"
    );
}


}

function showProfile() {


const element =
    document.getElementById(
        "profileContent"
    );

if (element) {

    element.classList.remove(
        "hidden"
    );
}


}

function hideProfile() {


const element =
    document.getElementById(
        "profileContent"
    );

if (element) {

    element.classList.add(
        "hidden"
    );
}


}

function showError(
message
) {


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


}

function hideError() {


const element =
    document.getElementById(
        "errorState"
    );

if (element) {

    element.classList.add(
        "hidden"
    );
}


}

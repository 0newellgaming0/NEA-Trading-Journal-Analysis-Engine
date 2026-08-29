"use strict";

document.addEventListener(
    "DOMContentLoaded",
    initializeTickerProfile
);

let tickerTradeRecords = [];
let currentTradeRecord = null;
let requestedTicker = null;

const ANALYSIS_DATA_PATH =
    "data/analysis";

const ANALYSIS_INDEX_PATH =
    "data/analysis/index.json";

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

        await initializeAnalysisDateSelector();

        const analysisDate =
            getSelectedAnalysisDate();

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
            findTickerTradeByDate(
                tickerTradeRecords,
                requestedTicker,
                analysisDate
            );

        if (!currentTradeRecord) {

            showError(
                `No trade record was published for ${requestedTicker} on ${analysisDate}.`
            );

            return;
        }

        renderTickerProfile(
            currentTradeRecord
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

function getSelectedAnalysisDate() {

    const selector =
        document.getElementById(
            "analysisDate"
        );

    if (
        selector &&
        selector.value
    ) {
        return selector.value;
    }

    return null;
}

async function initializeAnalysisDateSelector() {

    const selector =
        document.getElementById(
            "analysisDate"
        );

    if (!selector) {
        return;
    }

    selector.innerHTML = "";

    const response =
        await fetch(
            `${ANALYSIS_INDEX_PATH}?t=${Date.now()}`,
            {
                cache: "no-store"
            }
        );

    if (!response.ok) {

        throw new Error(
            `Unable to load ${ANALYSIS_INDEX_PATH}: ${response.status}`
        );
    }

    const indexData =
        await response.json();

    const dates =
        getTickerAnalysisDates(
            indexData,
            requestedTicker
        );

    if (!dates.length) {

        throw new Error(
            `No published analysis dates were found for ${requestedTicker}.`
        );
    }

    const requestedDate =
        getRequestedAnalysisDate();

    const selectedDate =
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
                formatAnalysisDate(
                    date
                );

            if (
                date === selectedDate
            ) {
                option.selected =
                    true;
            }

            selector.appendChild(
                option
            );
        }
    );
}

function getRequestedAnalysisDate() {

    const params =
        new URLSearchParams(
            window.location.search
        );

    const date =
        params.get("date");

    if (!date) {
        return null;
    }

    return date.trim() || null;
}

function getTickerAnalysisDates(
    indexData,
    ticker
) {

    if (
        !indexData ||
        typeof indexData !== "object"
    ) {
        return [];
    }

    const normalizedTicker =
        ticker.toUpperCase();

    if (
        indexData.tickers &&
        typeof indexData.tickers === "object" &&
        !Array.isArray(indexData.tickers)
    ) {

        const tickerEntry =
            indexData.tickers[
                normalizedTicker
            ];

        if (Array.isArray(tickerEntry)) {

            return normalizeAnalysisDates(
                tickerEntry
            );
        }

        if (
            tickerEntry &&
            typeof tickerEntry === "object"
        ) {

            for (
                const field of [
                    "dates",
                    "analysis_dates",
                    "available_dates"
                ]
            ) {

                if (
                    Array.isArray(
                        tickerEntry[field]
                    )
                ) {

                    return normalizeAnalysisDates(
                        tickerEntry[field]
                    );
                }
            }
        }
    }

    const directTicker =
        indexData[
            normalizedTicker
        ];

    if (
        Array.isArray(
            directTicker
        )
    ) {

        return normalizeAnalysisDates(
            directTicker
        );
    }

    if (
        directTicker &&
        typeof directTicker === "object"
    ) {

        for (
            const field of [
                "dates",
                "analysis_dates",
                "available_dates"
            ]
        ) {

            if (
                Array.isArray(
                    directTicker[field]
                )
            ) {

                return normalizeAnalysisDates(
                    directTicker[field]
                );
            }
        }
    }

    if (
        indexData.dates &&
        typeof indexData.dates === "object" &&
        !Array.isArray(indexData.dates)
    ) {

        const discoveredDates = [];

        Object.entries(
            indexData.dates
        ).forEach(
            (
                [date, tickers]
            ) => {

                if (
                    Array.isArray(tickers) &&
                    tickers.some(
                        value =>
                            String(value)
                                .toUpperCase() ===
                            normalizedTicker
                    )
                ) {

                    discoveredDates.push(
                        date
                    );
                }
            }
        );

        return normalizeAnalysisDates(
            discoveredDates
        );
    }

    if (
        Array.isArray(
            indexData.analyses
        )
    ) {

        const discoveredDates =
            indexData.analyses
                .filter(
                    item =>
                        item &&
                        typeof item === "object" &&
                        String(
                            item.ticker || ""
                        )
                            .toUpperCase() ===
                        normalizedTicker
                )
                .map(
                    item =>
                        item.date ||
                        item.analysis_date
                );

        return normalizeAnalysisDates(
            discoveredDates
        );
    }

    return [];
}

function normalizeAnalysisDates(
    dates
) {

    return [
        ...new Set(
            dates
                .map(
                    date =>
                        String(date)
                            .trim()
                )
                .filter(
                    date =>
                        /^\d{4}-\d{2}-\d{2}$/.test(
                            date
                        )
                )
        )
    ].sort(
        (
            a,
            b
        ) =>
            b.localeCompare(a)
    );
}

async function loadTickerTradeData(
    ticker
) {

    const url =
        `${ANALYSIS_DATA_PATH}/` +
        `${encodeURIComponent(ticker)}/` +
        `trades.json?t=${Date.now()}`;

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

function normalizeTradeData(
    data
) {

    let source = [];

    if (
        data &&
        Array.isArray(data.trades)
    ) {

        source =
            data.trades;
    }

    return source
        .map(
            normalizeTrade
        )
        .filter(
            Boolean
        );
}

function normalizeTrade(
    trade
) {

    if (
        !trade ||
        typeof trade !== "object"
    ) {
        return null;
    }

    if (
        trade.ticker === null ||
        trade.ticker === undefined ||
        String(
            trade.ticker
        ).trim() === ""
    ) {
        return null;
    }

    return {

        ticker:
            String(
                trade.ticker
            )
                .trim()
                .toUpperCase(),

        direction:
            displayValue(
                trade.direction
            ),

        status:
            displayValue(
                trade.status
            ),

        entry:
            numericValue(
                trade.entry
            ),

        currentPrice:
            numericValue(
                trade.current_price
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

        setup:
            displayValue(
                trade.setup
            ),

        regime:
            displayValue(
                trade.regime
            ),

        score:
            numericValue(
                trade.score
            ),

        updatedAt:
            trade.updated_at,

        analysisDate:
            normalizeTradeDate(
                trade.updated_at
            ),

        raw:
            trade
    };
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
        new Date(raw);

    if (
        Number.isNaN(
            date.getTime()
        )
    ) {
        return null;
    }

    return [
        date.getFullYear(),
        String(
            date.getMonth() + 1
        ).padStart(
            2,
            "0"
        ),
        String(
            date.getDate()
        ).padStart(
            2,
            "0"
        )
    ].join("-");
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

function bindAnalysisDateSelector() {

    const selector =
        document.getElementById(
            "analysisDate"
        );

    if (!selector) {
        return;
    }

    if (
        selector.dataset.tradeInitialized ===
        "true"
    ) {
        return;
    }

    selector.dataset.tradeInitialized =
        "true";

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

    if (!selectedDate) {
        return;
    }

    const trade =
        findTickerTradeByDate(
            tickerTradeRecords,
            requestedTicker,
            selectedDate
        );

    if (!trade) {

        showError(
            `No trade record was published for ${requestedTicker} on ${selectedDate}.`
        );

        return;
    }

    currentTradeRecord =
        trade;

    renderTickerProfile(
        trade
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
        "analysisGeneratedAt",
        formatTimestamp(
            trade.updatedAt
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
}

function buildOpportunityDescription(
    trade
) {

    let description =
        `${trade.ticker} is currently represented as a ` +
        `${trade.direction} ${trade.setup} opportunity ` +
        `within the published NEA28V1 ticker dataset.`;

    if (
        trade.regime !== "—"
    ) {

        description +=
            ` The current market regime is ${trade.regime}.`;
    }

    if (
        Number.isFinite(
            trade.score
        )
    ) {

        description +=
            ` The published NEA28V1 ranking score is ${formatScore(
                trade.score
            )}.`;
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

function formatTimestamp(
    value
) {

    if (
        value === null ||
        value === undefined ||
        value === ""
    ) {
        return "—";
    }

    let normalized =
        String(value).trim();

    if (
        /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?$/.test(
            normalized
        )
    ) {
        normalized += "Z";
    }

    const date =
        new Date(
            normalized
        );

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
            timeZone: "America/Chicago",
            month: "short",
            day: "numeric",
            year: "numeric",
            hour: "numeric",
            minute: "2-digit"
        }
    );
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
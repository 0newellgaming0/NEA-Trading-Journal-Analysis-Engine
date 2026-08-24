"use strict";

const TRADE_DATA_URL = "data/trades.json";

document.addEventListener(
    "DOMContentLoaded",
    initializeTickerProfile
);


async function initializeTickerProfile() {

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

        const rawData =
            await loadTradeData();

        const trades =
            normalizeTradeData(rawData);

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

        renderTickerProfile(trade);

    } catch (error) {

        console.error(
            "NEA28V1 ticker profile error:",
            error
        );

        showError(
            "Unable to load the current NEA28V1 publication dataset."
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

    return ticker
        .trim()
        .toUpperCase();
}


async function loadTradeData() {

    const response =
        await fetch(
            `${TRADE_DATA_URL}?t=${Date.now()}`,
            {
                cache: "no-store"
            }
        );

    if (!response.ok) {
        throw new Error(
            `Unable to load ${TRADE_DATA_URL}: ${response.status}`
        );
    }

    return await response.json();
}


function normalizeTradeData(data) {

    let source;

    if (Array.isArray(data)) {
        source = data;
    } else if (Array.isArray(data.trades)) {
        source = data.trades;
    } else if (Array.isArray(data.data)) {
        source = data.data;
    } else {
        source = [];
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

    return {

        ticker:
            String(ticker)
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
                trade.Setup
            ) || "Trade Setup",

        entry:
            numericValue(
                firstValue(
                    trade.entry,
                    trade.entry_price,
                    trade.Entry
                )
            ),

        stop:
            numericValue(
                firstValue(
                    trade.stop,
                    trade.stop_loss,
                    trade.Stop
                )
            ),

        target:
            numericValue(
                firstValue(
                    trade.target,
                    trade.target_price,
                    trade.Target
                )
            ),

        score:
            numericValue(
                firstValue(
                    trade.score,
                    trade.rank_score,
                    trade.Score
                )
            ),

        status:
            firstValue(
                trade.status,
                trade.Status
            ) || "—",

        raw: trade
    };
}


function findTickerTrade(
    trades,
    ticker
) {

    return trades.find(
        trade =>
            trade.ticker === ticker
    );
}


function renderTickerProfile(trade) {

    const rr =
        calculateRiskReward(
            trade.entry,
            trade.stop,
            trade.target,
            trade.direction
        );

    const risk =
        calculateRisk(
            trade.entry,
            trade.stop
        );

    const reward =
        calculateReward(
            trade.entry,
            trade.target
        );


    setText(
        "tickerSymbol",
        trade.ticker
    );

    setText(
        "tickerDirection",
        trade.direction
    );

    setText(
        "tickerSetup",
        trade.setup
    );

    setText(
        "tickerStatus",
        trade.status
    );


    setText(
        "entryPrice",
        formatPrice(trade.entry)
    );

    setText(
        "stopPrice",
        formatPrice(trade.stop)
    );

    setText(
        "targetPrice",
        formatPrice(trade.target)
    );

    setText(
        "tradeScore",
        formatScore(trade.score)
    );

    setText(
        "riskReward",
        formatRiskReward(rr)
    );


    setText(
        "analysisDirection",
        trade.direction
    );

    setText(
        "directionDescription",
        buildDirectionDescription(
            trade
        )
    );

    setText(
        "analysisSetup",
        trade.setup
    );

    setText(
        "analysisScore",
        formatScore(trade.score)
    );

    setText(
        "analysisStatus",
        trade.status
    );


    setText(
        "riskEntry",
        formatPrice(trade.entry)
    );

    setText(
        "riskAmount",
        formatPriceDistance(risk)
    );

    setText(
        "rewardAmount",
        formatPriceDistance(reward)
    );

    setText(
        "riskRatio",
        formatRiskReward(rr)
    );


    setText(
        "opportunityDescription",
        buildOpportunityDescription(
            trade,
            rr
        )
    );


    document.title =
        `NEA28V1 ${trade.ticker} Ticker Profile`;


    hideLoading();
    hideError();
    showProfile();
}


function buildDirectionDescription(trade) {

    const direction =
        String(
            trade.direction || ""
        ).toLowerCase();

    if (isLong(direction)) {

        return (
            `${trade.ticker} is currently represented as a ` +
            `bullish opportunity within the published ` +
            `NEA28V1 dataset.`
        );
    }

    if (isShort(direction)) {

        return (
            `${trade.ticker} is currently represented as a ` +
            `bearish opportunity within the published ` +
            `NEA28V1 dataset.`
        );
    }

    return (
        `${trade.ticker} is currently represented as a ` +
        `qualifying NEA28V1 trade opportunity.`
    );
}


function buildOpportunityDescription(
    trade,
    rr
) {

    const direction =
        String(
            trade.direction || ""
        ).toLowerCase();

    let description;

    if (isLong(direction)) {

        description =
            `${trade.ticker} is currently represented as a ` +
            `bullish ${trade.setup} opportunity.`;

    } else if (isShort(direction)) {

        description =
            `${trade.ticker} is currently represented as a ` +
            `bearish ${trade.setup} opportunity.`;

    } else {

        description =
            `${trade.ticker} is currently represented as a ` +
            `${trade.setup} opportunity.`;
    }

    if (Number.isFinite(trade.score)) {

        description +=
            ` The current NEA28V1 ranking score is ` +
            `${formatScore(trade.score)}.`;
    }

    if (Number.isFinite(rr)) {

        description +=
            ` The defined trade structure currently represents ` +
            `approximately ${formatRiskReward(rr)} of potential ` +
            `reward relative to defined risk.`;
    }

    description +=
        " Market conditions, liquidity, news, execution conditions, " +
        "and the underlying trade thesis should be independently " +
        "evaluated before making any trading decision.";

    return description;
}


function calculateRiskReward(
    entry,
    stop,
    target,
    direction
) {

    if (
        !Number.isFinite(entry) ||
        !Number.isFinite(stop) ||
        !Number.isFinite(target)
    ) {
        return null;
    }

    let risk;
    let reward;

    if (isShort(direction)) {

        risk =
            stop - entry;

        reward =
            entry - target;

    } else {

        risk =
            entry - stop;

        reward =
            target - entry;
    }

    if (
        risk <= 0 ||
        reward <= 0
    ) {
        return null;
    }

    return reward / risk;
}


function calculateRisk(
    entry,
    stop
) {

    if (
        !Number.isFinite(entry) ||
        !Number.isFinite(stop)
    ) {
        return null;
    }

    return Math.abs(
        entry - stop
    );
}


function calculateReward(
    entry,
    target
) {

    if (
        !Number.isFinite(entry) ||
        !Number.isFinite(target)
    ) {
        return null;
    }

    return Math.abs(
        target - entry
    );
}


function isLong(direction) {

    const value =
        String(
            direction || ""
        ).toLowerCase();

    return (
        value.includes("long") ||
        value.includes("bull") ||
        value.includes("buy")
    );
}


function isShort(direction) {

    const value =
        String(
            direction || ""
        ).toLowerCase();

    return (
        value.includes("short") ||
        value.includes("bear") ||
        value.includes("sell")
    );
}


function formatRiskReward(value) {

    if (!Number.isFinite(value)) {
        return "—";
    }

    return `${value.toFixed(2)}R`;
}


function formatPrice(value) {

    if (!Number.isFinite(value)) {
        return "—";
    }

    return `$${value.toFixed(2)}`;
}


function formatPriceDistance(value) {

    if (!Number.isFinite(value)) {
        return "—";
    }

    return `$${value.toFixed(2)}`;
}


function formatScore(value) {

    if (!Number.isFinite(value)) {
        return "—";
    }

    return Number.isInteger(value)
        ? String(value)
        : value.toFixed(2);
}


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
                .replace(/[$,%]/g, "")
                .trim()
        );

    return Number.isFinite(number)
        ? number
        : NaN;
}


function firstValue(...values) {

    for (const value of values) {

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


function setText(
    id,
    value
) {

    const element =
        document.getElementById(id);

    if (element) {
        element.textContent =
            value ?? "";
    }
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


function showError(message) {

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
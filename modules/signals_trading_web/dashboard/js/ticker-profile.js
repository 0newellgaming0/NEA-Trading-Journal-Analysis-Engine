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

        const data =
            await loadTradeData();

        const trades =
            normalizeTradeData(data);

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

    const ticker =
        trade.ticker;

    if (
        ticker === null ||
        ticker === undefined ||
        String(ticker).trim() === ""
    ) {
        return null;
    }

    return {

        ticker:
            String(ticker)
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
            trade.updated_at
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

    /*
     * PUBLIC FIELD: ticker
     */

    setText(
        "ticker",
        trade.ticker
    );


    /*
     * PUBLIC FIELD: direction
     */

    setText(
        "direction",
        trade.direction
    );


    /*
     * PUBLIC FIELD: setup
     */

    setText(
        "setup",
        trade.setup
    );


    /*
     * PUBLIC FIELD: regime
     */

    setText(
        "regime",
        trade.regime
    );


    /*
     * PUBLIC FIELD: timeframe
     */

    setText(
        "timeframe",
        trade.timeframe
    );


    /*
     * PUBLIC FIELD: entry
     */

    setText(
        "entry",
        formatPrice(
            trade.entry
        )
    );


    /*
     * PUBLIC FIELD: stop
     */

    setText(
        "stop",
        formatPrice(
            trade.stop
        )
    );


    /*
     * PUBLIC FIELD: target
     */

    setText(
        "target",
        formatPrice(
            trade.target
        )
    );


    /*
     * PUBLIC FIELD: risk_reward
     */

    setText(
        "riskReward",
        formatRiskReward(
            trade.riskReward
        )
    );


    /*
     * PUBLIC FIELD: score
     */

    setText(
        "score",
        formatScore(
            trade.score
        )
    );


    /*
     * PUBLIC FIELD: current_price
     */

    setText(
        "currentPrice",
        formatPrice(
            trade.currentPrice
        )
    );


    /*
     * PUBLIC FIELD: status
     */

    setText(
        "status",
        trade.status
    );


    /*
     * PUBLIC FIELD: signal_strength
     */

    setText(
        "signalStrength",
        trade.signalStrength
    );


    /*
     * PUBLIC FIELD: confluence
     */

    setText(
        "confluence",
        formatConfluence(
            trade.confluence
        )
    );


    /*
     * PUBLIC FIELD: created_at
     */

    setText(
        "createdAt",
        formatTimestamp(
            trade.createdAt
        )
    );


    /*
     * PUBLIC FIELD: updated_at
     */

    setText(
        "updatedAt",
        formatTimestamp(
            trade.updatedAt
        )
    );


    document.title =
        `NEA28V1 ${trade.ticker} Ticker Profile`;


    hideLoading();
    hideError();
    showProfile();
}


function numericValue(value) {

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
                .replace(/[$,%]/g, "")
                .trim()
        );

    return Number.isFinite(number)
        ? number
        : NaN;
}


function displayValue(value) {

    if (
        value === null ||
        value === undefined ||
        value === ""
    ) {
        return "—";
    }

    return String(value);
}


function formatPrice(value) {

    if (!Number.isFinite(value)) {
        return "—";
    }

    return `$${value.toFixed(4)}`;
}


function formatRiskReward(value) {

    if (!Number.isFinite(value)) {
        return "—";
    }

    return `${value.toFixed(2)}R`;
}


function formatScore(value) {

    if (!Number.isFinite(value)) {
        return "—";
    }

    return Number.isInteger(value)
        ? String(value)
        : value.toFixed(2);
}


function formatConfluence(value) {

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


function formatTimestamp(value) {

    if (
        value === null ||
        value === undefined ||
        value === ""
    ) {
        return "—";
    }

    const date =
        new Date(value);

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
            month: "short",
            day: "numeric",
            year: "numeric",
            hour: "numeric",
            minute: "2-digit"
        }
    );
}


function setText(
    id,
    value
) {

    const element =
        document.getElementById(id);

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
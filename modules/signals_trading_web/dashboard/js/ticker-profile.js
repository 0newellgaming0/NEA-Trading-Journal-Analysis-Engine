"use strict";

const TRADE_DATA_URL = "data/trades.json";

document.addEventListener(
    "DOMContentLoaded",
    initializeTickerProfile
);


async function initializeTickerProfile() {

    const ticker =
        getRequestedTicker();

    if (!ticker) {
        showError(
            "No ticker was specified. Open this page with a ticker parameter, such as ticker-profile.html?ticker=AAPL."
        );
        return;
    }

    try {

        const rawData =
            await loadTradeData();

        const trades =
            normalizeTradeData(rawData);

        if (!trades.length) {
            showError(
                "The NEA28V1 publication dataset does not currently contain any trade opportunities."
            );
            return;
        }

        const rankedTrades =
            rankTrades(trades);

        const trade =
            findTicker(
                rankedTrades,
                ticker
            );

        if (!trade) {
            showError(
                `Ticker ${ticker} was not found in the current NEA28V1 publication dataset.`
            );
            return;
        }

        renderProfile(
            trade,
            rankedTrades,
            rawData
        );

    } catch (error) {

        console.error(
            "NEA28V1 ticker profile error:",
            error
        );

        showError(
            "Unable to load the current NEA28V1 trade dataset."
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

        raw:
            trade
    };
}


function rankTrades(trades) {

    return [...trades].sort(
        (a, b) => {

            const scoreA =
                Number.isFinite(a.score)
                    ? a.score
                    : -Infinity;

            const scoreB =
                Number.isFinite(b.score)
                    ? b.score
                    : -Infinity;

            if (scoreB !== scoreA) {
                return scoreB - scoreA;
            }

            return a.ticker.localeCompare(
                b.ticker
            );
        }
    );
}


function findTicker(
    trades,
    ticker
) {

    return trades.find(
        trade =>
            trade.ticker === ticker
    ) || null;
}


function renderProfile(
    trade,
    rankedTrades,
    rawData
) {

    const rank =
        rankedTrades.findIndex(
            item =>
                item.ticker === trade.ticker
        ) + 1;

    const riskReward =
        calculateRiskReward(
            trade.entry,
            trade.stop,
            trade.target,
            trade.direction
        );

    setText(
        "tickerSymbol",
        trade.ticker
    );

    setText(
        "tickerSetup",
        trade.setup
    );

    setText(
        "tickerDirection",
        trade.direction
    );

    setText(
        "tickerStatus",
        trade.status
    );

    setText(
        "score",
        formatScore(trade.score)
    );

    setText(
        "rank",
        rank > 0
            ? `#${rank}`
            : "—"
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
        "entry",
        formatPrice(trade.entry)
    );

    setText(
        "stop",
        formatPrice(trade.stop)
    );

    setText(
        "target",
        formatPrice(trade.target)
    );

    setText(
        "riskReward",
        formatRiskReward(riskReward)
    );

    renderAnalysis(
        trade,
        rank
    );

    renderAssessment(
        trade,
        rank,
        riskReward
    );

    renderAdditionalData(
        trade.raw
    );

    document.title =
        `${trade.ticker} | NEA28V1 Ticker Profile`;

    showProfile();
}


function renderAnalysis(
    trade,
    rank
) {

    const direction =
        String(
            trade.direction || ""
        ).toLowerCase();

    let directionTitle =
        "Neutral";

    let directionDescription =
        "The published setup does not currently indicate a clearly defined bullish or bearish classification.";

    if (isLong(direction)) {

        directionTitle =
            "Bullish";

        directionDescription =
            `${trade.ticker} is currently represented as a bullish opportunity within the published NEA28V1 dataset.`;
    }

    if (isShort(direction)) {

        directionTitle =
            "Bearish";

        directionDescription =
            `${trade.ticker} is currently represented as a bearish opportunity within the published NEA28V1 dataset.`;
    }

    setText(
        "analysisDirection",
        directionTitle
    );

    setText(
        "analysisDirectionDescription",
        directionDescription
    );

    setText(
        "analysisSetup",
        trade.setup
    );

    setText(
        "analysisSetupDescription",
        `The current publication classifies ${trade.ticker} as ${trade.setup}.`
    );

    setText(
        "analysisRank",
        rank > 0
            ? `#${rank}`
            : "—"
    );

    const structured =
        Number.isFinite(trade.entry) &&
        Number.isFinite(trade.stop) &&
        Number.isFinite(trade.target);

    setText(
        "analysisStructure",
        structured
            ? "Structured"
            : "Incomplete"
    );

    setText(
        "analysisStructureDescription",
        structured
            ? "Entry, stop, and target values are available for risk/reward evaluation."
            : "One or more trade structure values are unavailable in the current dataset."
    );
}


function renderAssessment(
    trade,
    rank,
    riskReward
) {

    let assessment =
        `${trade.ticker} is currently represented in the NEA28V1 publication dataset as a ${trade.direction.toLowerCase()} ${trade.setup.toLowerCase()} opportunity.`;

    if (Number.isFinite(trade.score)) {

        assessment +=
            ` The setup currently carries a score of ${formatScore(trade.score)} and ranks #${rank} within the loaded publication dataset.`;
    }

    if (Number.isFinite(riskReward)) {

        assessment +=
            ` Its defined trade structure produces a calculated risk/reward ratio of ${formatRiskReward(riskReward)}.`;
    }

    assessment +=
        " This profile represents published system information and should not be interpreted as a guarantee of future performance.";

    setText(
        "tickerAssessment",
        assessment
    );
}


function renderAdditionalData(raw) {

    const container =
        document.getElementById(
            "additionalData"
        );

    if (!container) {
        return;
    }

    container.innerHTML = "";

    const excludedFields =
        new Set([
            "ticker",
            "symbol",
            "Ticker",
            "Symbol",
            "direction",
            "side",
            "Direction",
            "setup",
            "setup_type",
            "Setup",
            "entry",
            "entry_price",
            "Entry",
            "stop",
            "stop_loss",
            "Stop",
            "target",
            "target_price",
            "Target",
            "score",
            "rank_score",
            "Score",
            "status",
            "Status"
        ]);

    const fields =
        Object.entries(raw)
            .filter(
                ([key, value]) =>
                    !excludedFields.has(key) &&
                    value !== null &&
                    value !== undefined &&
                    value !== ""
            )
            .slice(0, 12);

    if (!fields.length) {

        container.innerHTML =
            `<div class="additional-item">
                <span>DATA</span>
                <strong>No additional published ticker fields.</strong>
             </div>`;

        return;
    }

    container.innerHTML =
        fields
            .map(
                ([key, value]) =>
                    `
                    <div class="additional-item">

                        <span>
                            ${escapeHtml(
                                formatFieldName(key)
                            )}
                        </span>

                        <strong>
                            ${escapeHtml(
                                formatFieldValue(value)
                            )}
                        </strong>

                    </div>
                    `
            )
            .join("");
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


function formatFieldName(value) {

    return String(value)
        .replace(/[_-]+/g, " ")
        .replace(/([a-z])([A-Z])/g, "$1 $2")
        .replace(/\b\w/g, char =>
            char.toUpperCase()
        );
}


function formatFieldValue(value) {

    if (
        typeof value === "object" &&
        value !== null
    ) {
        return JSON.stringify(value);
    }

    return String(value);
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


function showProfile() {

    const loading =
        document.getElementById(
            "loadingState"
        );

    const error =
        document.getElementById(
            "errorState"
        );

    const profile =
        document.getElementById(
            "profileContent"
        );

    if (loading) {
        loading.classList.add(
            "hidden"
        );
    }

    if (error) {
        error.classList.add(
            "hidden"
        );
    }

    if (profile) {
        profile.classList.remove(
            "hidden"
        );
    }
}


function showError(message) {

    const loading =
        document.getElementById(
            "loadingState"
        );

    const error =
        document.getElementById(
            "errorState"
        );

    const profile =
        document.getElementById(
            "profileContent"
        );

    if (loading) {
        loading.classList.add(
            "hidden"
        );
    }

    if (profile) {
        profile.classList.add(
            "hidden"
        );
    }

    if (error) {
        error.classList.remove(
            "hidden"
        );
    }

    setText(
        "errorMessage",
        message
    );
}


function escapeHtml(value) {

    return String(value ?? "")
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
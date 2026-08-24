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

        currentPrice:
            numericValue(
                firstValue(
                    trade.current_price,
                    trade.currentPrice,
                    trade.Current_Price,
                    trade.CurrentPrice
                )
            ),

        regime:
            firstValue(
                trade.regime,
                trade.Regime
            ) || "—",

        tradeType:
            firstValue(
                trade.trade_type,
                trade.tradeType,
                trade.Trade_Type,
                trade.TradeType
            ) || "—",

        setup:
            firstValue(
                trade.setup,
                trade.setup_type,
                trade.Setup
            ) || "Trade Setup",

        direction:
            firstValue(
                trade.direction,
                trade.side,
                trade.Direction
            ) || "—",

        status:
            firstValue(
                trade.status,
                trade.Status
            ) || "—",

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

        riskReward:
            numericValue(
                firstValue(
                    trade.risk_reward,
                    trade.riskReward,
                    trade.risk_reward_ratio,
                    trade.Risk_Reward
                )
            ),

        confidence:
            numericValue(
                firstValue(
                    trade.confidence,
                    trade.Confidence
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

        baseScore:
            numericValue(
                firstValue(
                    trade.base_score,
                    trade.baseScore,
                    trade.Base_Score
                )
            ),

        tradeProbability:
            numericValue(
                firstValue(
                    trade.trade_probability,
                    trade.tradeProbability,
                    trade.probability,
                    trade.Trade_Probability
                )
            ),

        probabilityConfidence:
            firstValue(
                trade.probability_confidence,
                trade.probabilityConfidence,
                trade.Probability_Confidence
            ) || "—",

        candidateCount:
            numericValue(
                firstValue(
                    trade.candidate_count,
                    trade.candidateCount,
                    trade.Candidate_Count
                )
            ),

        finvizContribution:
            numericValue(
                firstValue(
                    trade.finviz_contribution,
                    trade.finvizContribution,
                    trade.finviz_score,
                    trade.Finviz_Score
                )
            ),

        webullContribution:
            numericValue(
                firstValue(
                    trade.webull_contribution,
                    trade.webullContribution,
                    trade.webull_score,
                    trade.Webull_Score
                )
            ),

        canslimContribution:
            numericValue(
                firstValue(
                    trade.canslim_contribution,
                    trade.canslimContribution,
                    trade.canslim_score,
                    trade.CANSLIM_Score
                )
            ),

        updatedAt:
            firstValue(
                trade.updated_at,
                trade.updatedAt,
                trade.Updated_At,
                trade.updated
            ) || null,

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

    const calculatedRR =
        calculateRiskReward(
            trade.entry,
            trade.stop,
            trade.target,
            trade.direction
        );

    const rr =
        Number.isFinite(trade.riskReward)
            ? trade.riskReward
            : calculatedRR;

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


    /*
     * STATUS / UPDATED
     *
     * The profile status area uses the actual
     * publication timestamp from trades.json.
     *
     * "updated_at" is used instead of "detected".
     */

    setText(
        "tickerStatus",
        trade.status
    );

    setText(
        "tickerUpdated",
        formatUpdatedDate(
            trade.updatedAt
        )
    );


    /*
     * PRIMARY TRADE METRICS
     */

    setText(
        "currentPrice",
        formatPrice(
            trade.currentPrice
        )
    );

    setText(
        "entryPrice",
        formatPrice(
            trade.entry
        )
    );

    setText(
        "stopPrice",
        formatPrice(
            trade.stop
        )
    );

    setText(
        "targetPrice",
        formatPrice(
            trade.target
        )
    );

    setText(
        "tradeScore",
        formatScore(
            trade.score
        )
    );

    setText(
        "riskReward",
        formatRiskReward(
            rr
        )
    );


    /*
     * TRADE ANALYSIS
     */

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
        "analysisRegime",
        trade.regime
    );

    setText(
        "analysisTradeType",
        trade.tradeType
    );

    setText(
        "analysisSetup",
        trade.setup
    );

    setText(
        "analysisScore",
        formatScore(
            trade.score
        )
    );

    setText(
        "analysisStatus",
        trade.status
    );


    /*
     * CONFIDENCE MODEL
     */

    setText(
        "confidenceValue",
        formatNumber(
            trade.confidence
        )
    );

    setText(
        "baseScore",
        formatScore(
            trade.baseScore
        )
    );

    setText(
        "tradeProbability",
        formatPercent(
            trade.tradeProbability
        )
    );

    setText(
        "probabilityConfidence",
        trade.probabilityConfidence
    );


    /*
     * SIGNAL DATABASE SOURCE
     */

    setText(
        "candidateCount",
        formatNumber(
            trade.candidateCount
        )
    );

    setText(
        "finvizContribution",
        formatNumber(
            trade.finvizContribution
        )
    );

    setText(
        "webullContribution",
        formatNumber(
            trade.webullContribution
        )
    );

    setText(
        "canslimContribution",
        formatNumber(
            trade.canslimContribution
        )
    );


    /*
     * RISK FRAMEWORK
     */

    setText(
        "riskEntry",
        formatPrice(
            trade.entry
        )
    );

    setText(
        "riskAmount",
        formatPriceDistance(
            risk
        )
    );

    setText(
        "rewardAmount",
        formatPriceDistance(
            reward
        )
    );

    setText(
        "riskRatio",
        formatRiskReward(
            rr
        )
    );


    /*
     * OPPORTUNITY SUMMARY
     */

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


    if (trade.regime) {

        description +=
            ` The current market regime is ` +
            `${trade.regime}.`;
    }


    if (trade.tradeType) {

        description +=
            ` The trade is classified as ` +
            `${trade.tradeType}.`;
    }


    if (Number.isFinite(trade.score)) {

        description +=
            ` The current NEA28V1 ranking score is ` +
            `${formatScore(trade.score)}.`;
    }


    if (Number.isFinite(trade.confidence)) {

        description +=
            ` Confidence is ` +
            `${formatNumber(trade.confidence)}.`;
    }


    if (Number.isFinite(trade.tradeProbability)) {

        description +=
            ` The current trade probability is ` +
            `${formatPercent(trade.tradeProbability)}.`;
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

    return `$${value.toFixed(4)}`;
}


function formatPriceDistance(value) {

    if (!Number.isFinite(value)) {
        return "—";
    }

    return `$${value.toFixed(4)}`;
}


function formatScore(value) {

    if (!Number.isFinite(value)) {
        return "—";
    }

    return Number.isInteger(value)
        ? String(value)
        : value.toFixed(2);
}


function formatNumber(value) {

    if (!Number.isFinite(value)) {
        return "—";
    }

    return Number.isInteger(value)
        ? String(value)
        : value.toFixed(2);
}


function formatPercent(value) {

    if (!Number.isFinite(value)) {
        return "—";
    }

    return `${value.toFixed(2)}%`;
}


function formatUpdatedDate(value) {

    if (!value) {
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
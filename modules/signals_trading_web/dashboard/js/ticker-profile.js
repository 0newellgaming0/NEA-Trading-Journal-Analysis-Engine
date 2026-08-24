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

        const tickerRecords =
            findTickerTrades(
                trades,
                ticker
            );

        if (!tickerRecords.length) {
            showError(
                `No published NEA28V1 trade data was found for ${ticker}.`
            );
            return;
        }

        const trade =
            tickerRecords[
                tickerRecords.length - 1
            ];

        renderTickerProfile(
            trade,
            tickerRecords
        );

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

        currentPrice:
            numericValue(
                firstValue(
                    trade.current_price,
                    trade.currentPrice,
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
                trade.TradeType
            ) || "—",

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
                    trade.RiskReward,
                    trade.rr
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
                    trade.Score
                )
            ),

        baseScore:
            numericValue(
                firstValue(
                    trade.base_score,
                    trade.baseScore,
                    trade.BaseScore
                )
            ),

        tradeProbability:
            numericValue(
                firstValue(
                    trade.trade_probability,
                    trade.tradeProbability,
                    trade.TradeProbability
                )
            ),

        probabilityConfidence:
            firstValue(
                trade.probability_confidence,
                trade.probabilityConfidence,
                trade.ProbabilityConfidence
            ) || "—",

        candidateCount:
            numericValue(
                firstValue(
                    trade.candidate_count,
                    trade.candidates,
                    trade.CandidateCount
                )
            ),

        finvizScore:
            numericValue(
                firstValue(
                    trade.finviz_score,
                    trade.finviz,
                    trade.FinvizScore
                )
            ),

        webullScore:
            numericValue(
                firstValue(
                    trade.webull_score,
                    trade.webull,
                    trade.WebullScore
                )
            ),

        canslimScore:
            numericValue(
                firstValue(
                    trade.canslim_score,
                    trade.canslim,
                    trade.CANSLIMScore
                )
            ),

        database:
            firstValue(
                trade.database,
                trade.db,
                trade.Database
            ) || "—",

        /*
         * The publication profile uses UPDATED as the
         * signal/profile timestamp because DETECTED is
         * currently None in the source records.
         */
        updated:
            firstValue(
                trade.updated,
                trade.updated_at,
                trade.updatedAt,
                trade.Updated
            ),

        raw:
            trade
    };
}


function findTickerTrades(
    trades,
    ticker
) {

    return trades.filter(
        trade =>
            trade.ticker === ticker
    );
}


function renderTickerProfile(
    trade,
    tickerRecords
) {

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


    /*
     * HERO
     */

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
        "signalDetected",
        formatUpdatedDate(
            trade.updated
        )
    );


    /*
     * PRIMARY TRADE VALUES
     */

    setText(
        "currentPrice",
        formatPrice(
            trade.currentPrice
        )
    );

    setText(
        "regime",
        trade.regime
    );

    setText(
        "tradeType",
        trade.tradeType
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
     * ANALYSIS
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
     * RISK
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
     * CONFIDENCE MODEL
     */

    setText(
        "confidence",
        formatScore(
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
        formatScore(
            trade.tradeProbability
        )
    );

    setText(
        "probabilityConfidence",
        trade.probabilityConfidence
    );


    /*
     * DATABASE SOURCE
     */

    setText(
        "candidateCount",
        formatInteger(
            trade.candidateCount
        )
    );

    setText(
        "finvizScore",
        formatScore(
            trade.finvizScore
        )
    );

    setText(
        "webullScore",
        formatScore(
            trade.webullScore
        )
    );

    setText(
        "canslimScore",
        formatScore(
            trade.canslimScore
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


    /*
     * HISTORY
     */

    renderTradeHistory(
        tickerRecords
    );


    document.title =
        `NEA28V1 ${trade.ticker} Ticker Profile`;


    hideLoading();
    hideError();
    showProfile();
}


function renderTradeHistory(
    records
) {

    const container =
        document.getElementById(
            "tradeHistory"
        );

    if (!container) {
        return;
    }

    container.innerHTML = "";

    if (!records.length) {
        container.innerHTML =
            '<div class="no-history">No trade history available.</div>';

        return;
    }

    const sorted =
        [...records].reverse();

    for (const trade of sorted) {

        const article =
            document.createElement(
                "article"
            );

        article.className =
            "history-record";

        article.innerHTML = `
            <div class="history-head">
                <div>
                    <span class="section-label">DATABASE</span>
                    <strong>${escapeHtml(trade.database)}</strong>
                </div>

                <div class="history-updated">
                    <span>UPDATED</span>
                    <time>${escapeHtml(
                        formatUpdatedDate(
                            trade.updated
                        )
                    )}</time>
                </div>
            </div>

            <div class="history-grid">

                ${historyValue(
                    "TICKER",
                    trade.ticker
                )}

                ${historyValue(
                    "CURRENT PRICE",
                    formatPrice(
                        trade.currentPrice
                    )
                )}

                ${historyValue(
                    "REGIME",
                    trade.regime
                )}

                ${historyValue(
                    "TRADE TYPE",
                    trade.tradeType
                )}

                ${historyValue(
                    "SETUP",
                    trade.setup
                )}

                ${historyValue(
                    "DIRECTION",
                    trade.direction
                )}

                ${historyValue(
                    "STATUS",
                    trade.status
                )}

                ${historyValue(
                    "CONFIDENCE",
                    formatScore(
                        trade.confidence
                    )
                )}

                ${historyValue(
                    "ENTRY",
                    formatPrice(
                        trade.entry
                    )
                )}

                ${historyValue(
                    "STOP",
                    formatPrice(
                        trade.stop
                    )
                )}

                ${historyValue(
                    "TARGET",
                    formatPrice(
                        trade.target
                    )
                )}

                ${historyValue(
                    "RISK / REWARD",
                    formatRiskReward(
                        trade.riskReward
                    )
                )}

                ${historyValue(
                    "SCORE",
                    formatScore(
                        trade.score
                    )
                )}

                ${historyValue(
                    "CANDIDATES",
                    formatInteger(
                        trade.candidateCount
                    )
                )}

                ${historyValue(
                    "FINVIZ",
                    formatScore(
                        trade.finvizScore
                    )
                )}

                ${historyValue(
                    "WEBULL",
                    formatScore(
                        trade.webullScore
                    )
                )}

                ${historyValue(
                    "CANSLIM",
                    formatScore(
                        trade.canslimScore
                    )
                )}

            </div>
        `;

        container.appendChild(
            article
        );
    }
}


function historyValue(
    label,
    value
) {

    return `
        <div class="history-value">
            <span>${escapeHtml(label)}</span>
            <strong>${escapeHtml(
                value ?? "—"
            )}</strong>
        </div>
    `;
}


function buildDirectionDescription(
    trade
) {

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


function isLong(
    direction
) {

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


function isShort(
    direction
) {

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


function formatRiskReward(
    value
) {

    if (!Number.isFinite(value)) {
        return "—";
    }

    return `${value.toFixed(2)}R`;
}


function formatPrice(
    value
) {

    if (!Number.isFinite(value)) {
        return "—";
    }

    return `$${value.toFixed(2)}`;
}


function formatPriceDistance(
    value
) {

    if (!Number.isFinite(value)) {
        return "—";
    }

    return `$${value.toFixed(2)}`;
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


function formatInteger(
    value
) {

    if (!Number.isFinite(value)) {
        return "—";
    }

    return Math.round(value).toLocaleString(
        "en-US"
    );
}


function formatUpdatedDate(
    value
) {

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

    return new Intl.DateTimeFormat(
        "en-US",
        {
            month: "short",
            day: "numeric",
            year: "numeric",
            hour: "numeric",
            minute: "2-digit"
        }
    ).format(date);
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


function firstValue(
    ...values
) {

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


function escapeHtml(
    value
) {

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
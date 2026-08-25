"use strict";

const TRADE_DATA_URL = "data/trades.json";
const ANALYSIS_DATA_URL = "data/analysis_latest.json";

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

        let analysis = null;

        try {

            analysis =
                await loadAnalysisData();

        } catch (analysisError) {

            console.error(
                "NEA28V1 ticker profile analysis data error:",
                analysisError
            );
        }

        renderTickerProfile(
            trade,
            analysis,
            ticker
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


async function loadAnalysisData() {

    const response =
        await fetch(
            `${ANALYSIS_DATA_URL}?t=${Date.now()}`,
            {
                cache: "no-store"
            }
        );

    if (!response.ok) {

        throw new Error(
            `Unable to load ${ANALYSIS_DATA_URL}: ${response.status}`
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


function renderTickerProfile(
    trade,
    analysis,
    ticker
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

    renderAnalysisBlocks(
        analysis,
        ticker
    );

    document.title =
        `NEA28V1 ${trade.ticker} Ticker Profile`;

    hideLoading();
    hideError();
    showProfile();
}


function buildOpportunityDescription(trade) {

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
        `the published NEA28V1 dataset.`;

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


function renderAnalysisBlocks(
    analysis,
    ticker
) {

    const container =
        getOrCreateAnalysisContainer();

    if (!container) {
        return;
    }

    container.innerHTML = "";

    if (
        !analysis ||
        typeof analysis !== "object"
    ) {

        renderAnalysisUnavailable(
            container
        );

        return;
    }

    const requestedTicker =
        String(ticker)
            .trim()
            .toUpperCase();

    let tickerAnalysis = null;

    if (
        analysis.tickers &&
        typeof analysis.tickers === "object"
    ) {

        const tickerKeys =
            Object.keys(
                analysis.tickers
            );

        const matchingKey =
            tickerKeys.find(
                key =>
                    String(key)
                        .trim()
                        .toUpperCase() ===
                    requestedTicker
            );

        if (matchingKey) {

            tickerAnalysis =
                analysis.tickers[
                    matchingKey
                ];
        }
    }

    if (
        !tickerAnalysis &&
        analysis.ticker &&
        String(analysis.ticker)
            .trim()
            .toUpperCase() ===
            requestedTicker
    ) {

        tickerAnalysis =
            analysis;
    }

    if (
        !tickerAnalysis ||
        typeof tickerAnalysis !== "object"
    ) {

        renderAnalysisUnavailable(
            container
        );

        return;
    }

    const blocks =
        tickerAnalysis.analysis_blocks;

    if (
        !blocks ||
        typeof blocks !== "object"
    ) {

        renderAnalysisUnavailable(
            container
        );

        return;
    }

    renderAnalysisHeader(
        container,
        tickerAnalysis
    );

    Object.entries(
        blocks
    ).forEach(
        (
            [
                blockName,
                blockValue
            ]
        ) => {

            if (
                blockValue === null ||
                blockValue === undefined ||
                blockValue === ""
            ) {
                return;
            }

            renderAnalysisBlock(
                container,
                blockName,
                blockValue
            );
        }
    );
}


function getOrCreateAnalysisContainer() {

    let container =
        document.getElementById(
            "analysisBlocks"
        );

    if (container) {
        return container;
    }

    const profile =
        document.getElementById(
            "profileContent"
        );

    if (!profile) {
        return null;
    }

    container =
        document.createElement(
            "section"
        );

    container.id =
        "analysisBlocks";

    container.className =
        "analysis-section";

    const premium =
        profile.querySelector(
            ".premium"
        );

    if (premium) {

        profile.insertBefore(
            container,
            premium
        );

    } else {

        profile.appendChild(
            container
        );
    }

    return container;
}


function renderAnalysisHeader(
    container,
    analysis
) {

    const section =
        document.createElement(
            "section"
        );

    section.className =
        "analysis-header panel";

    const label =
        document.createElement(
            "span"
        );

    label.className =
        "section-label";

    label.textContent =
        "NEA28V1 ANALYSIS";

    const heading =
        document.createElement(
            "h2"
        );

    heading.textContent =
        "Ticker Intelligence";

    section.appendChild(
        label
    );

    section.appendChild(
        heading
    );

    if (analysis.generated_at) {

        const generated =
            document.createElement(
                "p"
            );

        generated.className =
            "analysis-generated";

        generated.textContent =
            `Analysis generated: ${formatTimestamp(
                analysis.generated_at
            )}`;

        section.appendChild(
            generated
        );
    }

    if (
        analysis.journal_timestamp !==
        undefined &&
        analysis.journal_timestamp !== ""
    ) {

        const journal =
            document.createElement(
                "p"
            );

        journal.className =
            "analysis-generated";

        journal.textContent =
            `Journal timestamp: ${formatTimestamp(
                analysis.journal_timestamp
            )}`;

        section.appendChild(
            journal
        );
    }

    if (
        analysis.stop_breached !==
        undefined
    ) {

        const stop =
            document.createElement(
                "p"
            );

        stop.className =
            "analysis-generated";

        stop.textContent =
            `Stop breached: ${
                analysis.stop_breached
                    ? "YES"
                    : "NO"
            }`;

        section.appendChild(
            stop
        );
    }

    container.appendChild(
        section
    );
}


function renderAnalysisBlock(
    container,
    blockName,
    blockValue
) {

    const article =
        document.createElement(
            "article"
        );

    article.className =
        "analysis-block";

    const heading =
        document.createElement(
            "h3"
        );

    heading.textContent =
        formatAnalysisTitle(
            blockName
        );

    article.appendChild(
        heading
    );

    if (
        typeof blockValue === "string"
    ) {

        const content =
            document.createElement(
                "pre"
            );

        content.className =
            "analysis-content";

        content.textContent =
            normalizeAnalysisText(
                blockValue
            );

        article.appendChild(
            content
        );

    } else {

        const content =
            document.createElement(
                "pre"
            );

        content.className =
            "analysis-content";

        content.textContent =
            JSON.stringify(
                blockValue,
                null,
                2
            );

        article.appendChild(
            content
        );
    }

    container.appendChild(
        article
    );
}


function renderAnalysisUnavailable(
    container
) {

    const section =
        document.createElement(
            "section"
        );

    section.className =
        "analysis-header panel";

    const label =
        document.createElement(
            "span"
        );

    label.className =
        "section-label";

    label.textContent =
        "NEA28V1 ANALYSIS";

    const heading =
        document.createElement(
            "h2"
        );

    heading.textContent =
        "Analysis Unavailable";

    const message =
        document.createElement(
            "p"
        );

    message.textContent =
        "No published analysis data is currently available for this ticker.";

    section.appendChild(
        label
    );

    section.appendChild(
        heading
    );

    section.appendChild(
        message
    );

    container.appendChild(
        section
    );
}


function formatAnalysisTitle(
    value
) {

    return String(value)
        .replace(
            /^sec_/,
            ""
        )
        .replace(
            /_/g,
            " "
        )
        .replace(
            /\b\w/g,
            character =>
                character.toUpperCase()
        );
}


function normalizeAnalysisText(
    value
) {

    return String(value)
        .replace(
            /\r\n/g,
            "\n"
        )
        .replace(
            /\n{4,}/g,
            "\n\n\n"
        )
        .trim();
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
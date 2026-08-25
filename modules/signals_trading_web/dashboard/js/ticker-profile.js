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
        const [
            tradeData,
            analysisData
        ] = await Promise.all([
            loadTradeData(),
            loadAnalysisData()
        ]);

        const trades =
            normalizeTradeData(
                tradeData
            );

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

        renderTickerProfile(
            trade,
            analysisData
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
    analysisData
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
        analysisData,
        trade.ticker
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
    analysisData,
    ticker
) {
    const analysisBlocks =
        getAnalysisBlocks(
            analysisData
        );

    const container =
        getAnalysisContainer();

    if (!container) {
        console.error(
            "NEA28V1 ticker profile: unable to create analysis container."
        );
        return;
    }

    container.innerHTML = "";

    if (
        !analysisBlocks ||
        Object.keys(analysisBlocks).length === 0
    ) {
        container.appendChild(
            createAnalysisMessage(
                "No analysis blocks were published for this ticker."
            )
        );
        return;
    }

    const analysisHeader =
        document.createElement(
            "div"
        );

    analysisHeader.className =
        "ticker-analysis-header";

    const heading =
        document.createElement(
            "h2"
        );

    heading.textContent =
        "NEA28V1 Analysis";

    analysisHeader.appendChild(
        heading
    );

    if (
        analysisData &&
        analysisData.generated_at
    ) {
        const generated =
            document.createElement(
                "div"
            );

        generated.className =
            "ticker-analysis-generated";

        generated.textContent =
            `Generated: ${formatTimestamp(
                analysisData.generated_at
            )}`;

        analysisHeader.appendChild(
            generated
        );
    }

    if (
        analysisData &&
        analysisData.stop_breached !== undefined
    ) {
        const stopStatus =
            document.createElement(
                "div"
            );

        stopStatus.className =
            "ticker-analysis-stop-status";

        stopStatus.textContent =
            analysisData.stop_breached
                ? "Stop Loss Status: BREACHED"
                : "Stop Loss Status: NOT BREACHED";

        analysisHeader.appendChild(
            stopStatus
        );
    }

    container.appendChild(
        analysisHeader
    );

    Object.entries(
        analysisBlocks
    ).forEach(
        (
            [
                blockName,
                blockContent
            ],
            index
        ) => {
            const block =
                createAnalysisBlock(
                    blockName,
                    blockContent,
                    index
                );

            container.appendChild(
                block
            );
        }
    );
}

function getAnalysisBlocks(
    analysisData
) {
    if (
        !analysisData ||
        typeof analysisData !== "object"
    ) {
        return {};
    }

    if (
        analysisData.analysis_blocks &&
        typeof analysisData.analysis_blocks === "object"
    ) {
        return analysisData.analysis_blocks;
    }

    return {};
}

function getAnalysisContainer() {
    let container =
        document.getElementById(
            "analysisBlocks"
        );

    if (container) {
        return container;
    }

    const profileContent =
        document.getElementById(
            "profileContent"
        );

    if (!profileContent) {
        return null;
    }

    container =
        document.createElement(
            "section"
        );

    container.id =
        "analysisBlocks";

    container.className =
        "ticker-analysis-blocks";

    profileContent.appendChild(
        container
    );

    return container;
}

function createAnalysisBlock(
    blockName,
    blockContent,
    index
) {
    const section =
        document.createElement(
            "section"
        );

    section.className =
        "ticker-analysis-block";

    section.dataset.analysisKey =
        blockName;

    section.dataset.analysisIndex =
        String(index);

    const title =
        document.createElement(
            "h3"
        );

    title.className =
        "ticker-analysis-block-title";

    title.textContent =
        formatAnalysisTitle(
            blockName
        );

    section.appendChild(
        title
    );

    const content =
        document.createElement(
            "div"
        );

    content.className =
        "ticker-analysis-block-content";

    content.textContent =
        normalizeAnalysisText(
            blockContent
        );

    section.appendChild(
        content
    );

    return section;
}

function createAnalysisMessage(
    message
) {
    const element =
        document.createElement(
            "div"
        );

    element.className =
        "ticker-analysis-message";

    element.textContent =
        message;

    return element;
}

function formatAnalysisTitle(
    blockName
) {
    if (!blockName) {
        return "Analysis";
    }

    return String(blockName)
        .replace(/^sec_/i, "")
        .replace(/_/g, " ")
        .replace(
            /\b\w/g,
            character =>
                character.toUpperCase()
        );
}

function normalizeAnalysisText(
    value
) {
    if (
        value === null ||
        value === undefined
    ) {
        return "—";
    }

    if (
        typeof value === "string"
    ) {
        return value.trim();
    }

    try {
        return JSON.stringify(
            value,
            null,
            2
        );
    } catch (error) {
        return String(value);
    }
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
    if (
        !Number.isFinite(value)
    ) {
        return "—";
    }

    return `$${value.toFixed(4)}`;
}

function formatRiskReward(value) {
    if (
        !Number.isFinite(value)
    ) {
        return "—";
    }

    return `${value.toFixed(2)}R`;
}

function formatScore(value) {
    if (
        !Number.isFinite(value)
    ) {
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
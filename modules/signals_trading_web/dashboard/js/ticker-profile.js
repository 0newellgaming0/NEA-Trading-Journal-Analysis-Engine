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

        const analysis =
            await loadAnalysisData(
                ticker
            );

        renderTickerProfile(
            trade,
            analysis
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

async function loadAnalysisData(ticker) {

    const response =
        await fetch(
            `${ANALYSIS_DATA_URL}?t=${Date.now()}`,
            {
                cache: "no-store"
            }
        );

    if (!response.ok) {

        console.warn(
            `Unable to load ${ANALYSIS_DATA_URL}: ${response.status}`
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

    const analysisTicker =
        data.ticker === null ||
        data.ticker === undefined
            ? ""
            : String(data.ticker)
                .trim()
                .toUpperCase();

    if (
        analysisTicker !== ticker
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
    analysis
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

    renderAnalysis(
        analysis
    );

    document.title =
        `NEA28V1 ${trade.ticker} Ticker Profile`;

    hideLoading();
    hideError();
    showProfile();
}

function renderAnalysis(analysis) {

    const section =
        document.getElementById(
            "analysisSection"
        );

    const container =
        document.getElementById(
            "analysisBlocks"
        );

    const emptyState =
        document.getElementById(
            "analysisEmpty"
        );

    if (
        !section ||
        !container
    ) {
        return;
    }

    container.innerHTML = "";

    if (emptyState) {
        emptyState.classList.add("hidden");
    }

    if (
        !analysis ||
        !analysis.analysis_blocks ||
        typeof analysis.analysis_blocks !== "object"
    ) {

        section.classList.add("hidden");

        if (emptyState) {
            emptyState.classList.remove("hidden");
        }

        renderAnalysisMetadata(null);

        return;
    }

    const blocks =
        analysis.analysis_blocks;

    const keys =
        Object.keys(blocks);

    if (!keys.length) {

        section.classList.add("hidden");

        if (emptyState) {
            emptyState.classList.remove("hidden");
        }

        renderAnalysisMetadata(
            analysis
        );

        return;
    }

    let renderedCount = 0;

    keys.forEach(
        (
            key,
            index
        ) => {

            const value =
                blocks[key];

            if (
                value === null ||
                value === undefined
            ) {
                return;
            }

            const card =
                document.createElement(
                    "article"
                );

            card.className =
                "analysis-card";

            card.dataset.analysisKey =
                key;

            card.dataset.analysisIndex =
                String(index + 1);

            const header =
                document.createElement(
                    "div"
                );

            header.className =
                "analysis-card-header";

            const indexLabel =
                document.createElement(
                    "span"
                );

            indexLabel.className =
                "analysis-card-index";

            indexLabel.textContent =
                String(index + 1).padStart(
                    2,
                    "0"
                );

            const title =
                document.createElement(
                    "h3"
                );

            title.textContent =
                formatAnalysisTitle(
                    key
                );

            header.appendChild(
                indexLabel
            );

            header.appendChild(
                title
            );

            const content =
                document.createElement(
                    "div"
                );

            content.className =
                "analysis-card-content";

            renderAnalysisValue(
                content,
                value
            );

            const source =
                createSourceReport(
                    value
                );

            card.appendChild(
                header
            );

            card.appendChild(
                content
            );

            if (source) {
                card.appendChild(
                    source
                );
            }

            container.appendChild(
                card
            );

            renderedCount += 1;
        }
    );

    renderAnalysisMetadata(
        analysis
    );

    if (!renderedCount) {

        section.classList.add("hidden");

        if (emptyState) {
            emptyState.classList.remove("hidden");
        }

        return;
    }

    section.classList.remove(
        "hidden"
    );
}

function createSourceReport(value) {

    if (
        typeof value !== "string" ||
        !value.trim()
    ) {
        return null;
    }

    const details =
        document.createElement(
            "details"
        );

    details.className =
        "analysis-source"
        ;

    const summary =
        document.createElement(
            "summary"
        );

    summary.textContent =
        "SOURCE REPORT";

    const pre =
        document.createElement(
            "pre"
        );

    pre.textContent =
        value;

    details.appendChild(
        summary
    );

    details.appendChild(
        pre
    );

    return details;
}

function renderAnalysisMetadata(
    analysis
) {

    const generatedAt =
        document.getElementById(
            "analysisGeneratedAt"
        );

    const generatedAtMeta =
        document.getElementById(
            "analysisGeneratedAtMeta"
        );

    const journalTimestamp =
        document.getElementById(
            "analysisJournalTimestamp"
        );

    const stopBreached =
        document.getElementById(
            "analysisStopBreached"
        );

    const riskSection =
        document.getElementById(
            "analysisRiskSection"
        );

    const stopBreachStatus =
        document.getElementById(
            "stopBreachStatus"
        );

    const generated =
        analysis &&
        analysis.generated_at
            ? formatTimestamp(
                analysis.generated_at
            )
            : "—";

    const journal =
        analysis &&
        analysis.journal_timestamp
            ? formatTimestamp(
                analysis.journal_timestamp
            )
            : "—";

    const breached =
        Boolean(
            analysis &&
            analysis.stop_breached === true
        );

    if (generatedAt) {
        generatedAt.textContent =
            generated;
    }

    if (generatedAtMeta) {
        generatedAtMeta.textContent =
            generated;
    }

    if (journalTimestamp) {
        journalTimestamp.textContent =
            journal;
    }

    if (stopBreached) {

        stopBreached.textContent =
            breached
                ? "STOP BREACHED"
                : "STOP NOT BREACHED";

        stopBreached.className =
            breached
                ? "analysis-status breached"
                : "analysis-status clear";
    }

    if (stopBreachStatus) {

        stopBreachStatus.textContent =
            breached
                ? "STOP STATUS: STOP BREACHED"
                : "STOP STATUS: STOP NOT BREACHED";

        stopBreachStatus.className =
            breached
                ? "analysis-status breached"
                : "analysis-status clear";
    }

    if (riskSection) {

        if (analysis) {
            riskSection.classList.remove(
                "hidden"
            );
        } else {
            riskSection.classList.add(
                "hidden"
            );
        }
    }
}

function renderAnalysisValue(
    container,
    value
) {

    if (
        typeof value === "string"
    ) {

        renderAnalysisText(
            container,
            value
        );

        return;
    }

    if (Array.isArray(value)) {

        renderAnalysisArray(
            container,
            value
        );

        return;
    }

    if (
        value &&
        typeof value === "object"
    ) {

        renderAnalysisObject(
            container,
            value
        );

        return;
    }

    const paragraph =
        document.createElement(
            "p"
        );

    paragraph.textContent =
        formatAnalysisScalar(
            value
        );

    container.appendChild(
        paragraph
    );
}

function renderAnalysisText(
    container,
    text
) {

    const normalized =
        text
            .replace(
                /\r\n/g,
                "\n"
            )
            .trim();

    if (!normalized) {
        return;
    }

    const embeddedJson =
        extractEmbeddedJson(
            normalized
        );

    if (embeddedJson) {

        const before =
            normalized.slice(
                0,
                embeddedJson.start
            ).trim();

        const after =
            normalized.slice(
                embeddedJson.end
            ).trim();

        if (before) {
            renderAnalysisReportText(
                container,
                before
            );
        }

        const jsonContainer =
            document.createElement(
                "div"
            );

        jsonContainer.className =
            "analysis-embedded-json";

        renderAnalysisValue(
            jsonContainer,
            embeddedJson.value
        );

        container.appendChild(
            jsonContainer
        );

        if (after) {
            renderAnalysisReportText(
                container,
                after
            );
        }

        return;
    }

    renderAnalysisReportText(
        container,
        normalized
    );
}

function renderAnalysisReportText(
    container,
    text
) {

    const lines =
        text.split("\n");

    let paragraphLines = [];
    let fieldRows = [];

    function flushParagraph() {

        if (!paragraphLines.length) {
            return;
        }

        const paragraph =
            document.createElement(
                "p"
            );

        paragraph.textContent =
            paragraphLines
                .join(" ")
                .trim();

        container.appendChild(
            paragraph
        );

        paragraphLines = [];
    }

    function flushFields() {

        if (!fieldRows.length) {
            return;
        }

        const fields =
            document.createElement(
                "div"
            );

        fields.className =
            "analysis-data";

        fieldRows.forEach(
            row => {

                const item =
                    document.createElement(
                        "div"
                    );

                item.className =
                    "analysis-data-item";

                const label =
                    document.createElement(
                        "span"
                    );

                label.textContent =
                    formatAnalysisTitle(
                        row.key
                    );

                const output =
                    document.createElement(
                        "strong"
                    );

                output.textContent =
                    row.value;

                item.appendChild(
                    label
                );

                item.appendChild(
                    output
                );

                fields.appendChild(
                    item
                );
            }
        );

        container.appendChild(
            fields
        );

        fieldRows = [];
    }

    function flushAll() {
        flushParagraph();
        flushFields();
    }

    lines.forEach(
        line => {

            const trimmed =
                line.trim();

            if (!trimmed) {

                flushAll();

                return;
            }

            const headingMatch =
                trimmed.match(
                    /^(#{1,6})\s+(.+)$/
                );

            if (headingMatch) {

                flushAll();

                const level =
                    Math.min(
                        headingMatch[1].length + 1,
                        6
                    );

                const heading =
                    document.createElement(
                        `h${level}`
                    );

                heading.textContent =
                    headingMatch[2]
                        .trim();

                heading.className =
                    "analysis-report-heading";

                container.appendChild(
                    heading
                );

                return;
            }

            const fieldMatch =
                trimmed.match(
                    /^([^:]{1,120}):\s*(.+)$/
                );

            if (
                fieldMatch &&
                !trimmed.startsWith(
                    "http:"
                ) &&
                !trimmed.startsWith(
                    "https:"
                )
            ) {

                flushParagraph();

                fieldRows.push({
                    key:
                        fieldMatch[1]
                            .trim(),

                    value:
                        fieldMatch[2]
                            .trim()
                });

                return;
            }

            if (
                fieldRows.length &&
                !trimmed.includes(":")
            ) {

                fieldRows[
                    fieldRows.length - 1
                ].value +=
                    ` ${trimmed}`;

                return;
            }

            flushFields();

            paragraphLines.push(
                trimmed
            );
        }
    );

    flushAll();
}

function extractEmbeddedJson(
    text
) {

    const firstBrace =
        text.search(
            /[\[{]/
        );

    if (firstBrace < 0) {
        return null;
    }

    const candidate =
        text.slice(
            firstBrace
        );

    const parsed =
        parseJsonPrefix(
            candidate
        );

    if (!parsed) {
        return null;
    }

    return {
        start:
            firstBrace,

        end:
            firstBrace +
            parsed.length,

        value:
            parsed.value
    };
}

function parseJsonPrefix(
    text
) {

    const first =
        text[0];

    if (
        first !== "{" &&
        first !== "["
    ) {
        return null;
    }

    let depth = 0;
    let inString = false;
    let escaped = false;

    for (
        let i = 0;
        i < text.length;
        i += 1
    ) {

        const character =
            text[i];

        if (inString) {

            if (escaped) {

                escaped = false;

                continue;
            }

            if (
                character === "\\"
            ) {

                escaped = true;

                continue;
            }

            if (
                character === "\""
            ) {

                inString = false;
            }

            continue;
        }

        if (
            character === "\""
        ) {

            inString = true;

            continue;
        }

        if (
            character === "{" ||
            character === "["
        ) {

            depth += 1;

            continue;
        }

        if (
            character === "}" ||
            character === "]"
        ) {

            depth -= 1;

            if (depth === 0) {

                const candidate =
                    text.slice(
                        0,
                        i + 1
                    );

                try {

                    return {
                        value:
                            JSON.parse(
                                candidate
                            ),

                        length:
                            i + 1
                    };

                } catch (
                    error
                ) {

                    return null;
                }
            }
        }
    }

    return null;
}

function renderAnalysisArray(
    container,
    items
) {

    if (!items.length) {
        return;
    }

    const list =
        document.createElement(
            "div"
        );

    list.className =
        "analysis-list";

    items.forEach(
        (
            item,
            index
        ) => {

            const itemElement =
                document.createElement(
                    "div"
                );

            itemElement.className =
                "analysis-list-item";

            const indexLabel =
                document.createElement(
                    "span"
                );

            indexLabel.className =
                "analysis-list-index";

            indexLabel.textContent =
                `ITEM ${index + 1}`;

            itemElement.appendChild(
                indexLabel
            );

            renderAnalysisValue(
                itemElement,
                item
            );

            list.appendChild(
                itemElement
            );
        }
    );

    container.appendChild(
        list
    );
}

function renderAnalysisObject(
    container,
    object
) {

    const data =
        document.createElement(
            "div"
        );

    data.className =
        "analysis-data analysis-object";

    Object.entries(
        object
    ).forEach(
        (
            [key, value]
        ) => {

            const item =
                document.createElement(
                    "div"
                );

            item.className =
                "analysis-data-item analysis-object-item";

            const label =
                document.createElement(
                    "span"
                );

            label.textContent =
                formatAnalysisTitle(
                    key
                );

            item.appendChild(
                label
            );

            if (
                value &&
                typeof value === "object"
            ) {

                const nested =
                    document.createElement(
                        "div"
                    );

                nested.className =
                    "analysis-nested";

                renderAnalysisValue(
                    nested,
                    value
                );

                item.appendChild(
                    nested
                );

            } else {

                const output =
                    document.createElement(
                        "strong"
                    );

                output.textContent =
                    formatAnalysisScalar(
                        value
                    );

                item.appendChild(
                    output
                );
            }

            data.appendChild(
                item
            );
        }
    );

    container.appendChild(
        data
    );
}

function formatAnalysisScalar(
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
        typeof value === "boolean"
    ) {
        return value
            ? "Yes"
            : "No";
    }

    if (
        typeof value === "number"
    ) {

        if (
            !Number.isFinite(
                value
            )
        ) {
            return "—";
        }

        return String(value);
    }

    return String(value);
}

function formatAnalysisTitle(
    key
) {

    return String(key)
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
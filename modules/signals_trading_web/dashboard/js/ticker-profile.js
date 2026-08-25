"use strict";

const TRADE_DATA_URL = "data/trades.json";
const ANALYSIS_DATA_URL = "data/analysis_latest.json";

document.addEventListener(
    "DOMContentLoaded",
    initializeTickerProfile
);

async function initializeTickerProfile() {

    showLoading();
    hideError();
    hideProfile();

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

    const normalized =
        ticker
            .trim()
            .toUpperCase();

    return normalized || null;
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
        typeof data !== "object" ||
        Array.isArray(data)
    ) {

        console.warn(
            `${ANALYSIS_DATA_URL} does not contain a valid ticker-indexed object.`
        );

        return null;
    }

    /*
     * Correct publication schema:
     *
     * {
     *     "ARI": {
     *         "ticker": "ARI",
     *         "generated_at": "...",
     *         "journal_timestamp": "",
     *         "stop_breached": false,
     *         "analysis_blocks": {
     *             ...
     *         }
     *     },
     *
     *     "BCAB": {
     *         "ticker": "BCAB",
     *         ...
     *     }
     * }
     *
     * Resolve directly from the root-level ticker index.
     */

    const tickerAnalysis =
        data[ticker];

    if (
        !tickerAnalysis ||
        typeof tickerAnalysis !== "object" ||
        Array.isArray(tickerAnalysis)
    ) {

        console.warn(
            `No analysis entry exists for ticker ${ticker}.`
        );

        return null;
    }

    const analysisTicker =
        tickerAnalysis.ticker === null ||
        tickerAnalysis.ticker === undefined
            ? ""
            : String(
                tickerAnalysis.ticker
            )
                .trim()
                .toUpperCase();

    if (
        analysisTicker &&
        analysisTicker !== ticker
    ) {

        console.warn(
            `Analysis ticker mismatch: requested ${ticker}, received ${analysisTicker}.`
        );

        return null;
    }

    if (
        !tickerAnalysis.analysis_blocks ||
        typeof tickerAnalysis.analysis_blocks !== "object" ||
        Array.isArray(tickerAnalysis.analysis_blocks)
    ) {

        console.warn(
            `Analysis entry for ${ticker} does not contain a valid analysis_blocks object.`
        );

        return null;
    }

    return tickerAnalysis;
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

    const riskSection =
        document.getElementById(
            "analysisRiskSection"
        );

    const stopBreachStatus =
        document.getElementById(
            "stopBreachStatus"
        );

    if (container) {
        container.innerHTML = "";
    }

    renderAnalysisMetadata(
        analysis
    );

    renderAnalysisRisk(
        analysis
    );

    if (
        !analysis ||
        !analysis.analysis_blocks ||
        typeof analysis.analysis_blocks !== "object" ||
        Array.isArray(analysis.analysis_blocks)
    ) {

        if (section) {
            section.classList.add("hidden");
        }

        if (emptyState) {
            emptyState.classList.remove("hidden");
        }

        if (riskSection) {
            riskSection.classList.add("hidden");
        }

        if (stopBreachStatus) {
            stopBreachStatus.textContent =
                "STOP STATUS: —";
            stopBreachStatus.className =
                "analysis-status";
        }

        return;
    }

    const blocks =
        analysis.analysis_blocks;

    const keys =
        Object.keys(blocks);

    if (!keys.length) {

        if (section) {
            section.classList.add("hidden");
        }

        if (emptyState) {
            emptyState.classList.remove("hidden");
        }

        if (riskSection) {
            riskSection.classList.add("hidden");
        }

        return;
    }

    if (emptyState) {
        emptyState.classList.add("hidden");
    }

    keys.forEach(
        (
            key,
            index
        ) => {

            const value =
                blocks[key];

            if (
                value === null ||
                value === undefined ||
                value === ""
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
        }
    );

    if (
        container.children.length === 0
    ) {

        if (section) {
            section.classList.add("hidden");
        }

        if (emptyState) {
            emptyState.classList.remove("hidden");
        }

        return;
    }

    if (section) {
        section.classList.remove("hidden");
    }
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

    const generatedValue =
        analysis &&
        analysis.generated_at
            ? formatTimestamp(
                analysis.generated_at
            )
            : "—";

    if (generatedAt) {

        generatedAt.textContent =
            generatedValue;
    }

    if (generatedAtMeta) {

        generatedAtMeta.textContent =
            generatedValue;
    }

    if (journalTimestamp) {

        journalTimestamp.textContent =
            analysis &&
            analysis.journal_timestamp
                ? formatTimestamp(
                    analysis.journal_timestamp
                )
                : "—";
    }

    if (stopBreached) {

        if (
            analysis &&
            analysis.stop_breached === true
        ) {

            stopBreached.textContent =
                "STOP BREACHED";

            stopBreached.className =
                "analysis-status breached";

        } else if (
            analysis &&
            analysis.stop_breached === false
        ) {

            stopBreached.textContent =
                "STOP NOT BREACHED";

            stopBreached.className =
                "analysis-status clear";

        } else {

            stopBreached.textContent =
                "—";

            stopBreached.className =
                "analysis-status";
        }
    }
}

function renderAnalysisRisk(
    analysis
) {

    const riskSection =
        document.getElementById(
            "analysisRiskSection"
        );

    const stopBreachStatus =
        document.getElementById(
            "stopBreachStatus"
        );

    if (
        !riskSection ||
        !stopBreachStatus
    ) {
        return;
    }

    if (
        !analysis ||
        typeof analysis !== "object" ||
        !Object.prototype.hasOwnProperty.call(
            analysis,
            "stop_breached"
        )
    ) {

        riskSection.classList.add(
            "hidden"
        );

        stopBreachStatus.textContent =
            "STOP STATUS: —";

        stopBreachStatus.className =
            "analysis-status";

        return;
    }

    riskSection.classList.remove(
        "hidden"
    );

    if (
        analysis.stop_breached === true
    ) {

        stopBreachStatus.textContent =
            "STOP STATUS: STOP BREACHED";

        stopBreachStatus.className =
            "analysis-status breached";

        return;
    }

    if (
        analysis.stop_breached === false
    ) {

        stopBreachStatus.textContent =
            "STOP STATUS: STOP NOT BREACHED";

        stopBreachStatus.className =
            "analysis-status clear";

        return;
    }

    stopBreachStatus.textContent =
        "STOP STATUS: —";

    stopBreachStatus.className =
        "analysis-status";
}

function renderAnalysisValue(
    container,
    value
) {

    if (
        typeof value === "string"
    ) {

        const embeddedJson =
            extractEmbeddedJson(
                value
            );

        if (embeddedJson) {

            renderAnalysisText(
                container,
                embeddedJson.before
            );

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

            renderAnalysisText(
                container,
                embeddedJson.after
            );

            return;
        }

        renderAnalysisText(
            container,
            value
        );

        return;
    }

    if (
        Array.isArray(value)
    ) {

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

    if (
        text === null ||
        text === undefined
    ) {
        return;
    }

    const normalized =
        String(text)
            .replace(
                /\r\n/g,
                "\n"
            )
            .trim();

    if (!normalized) {
        return;
    }

    const lines =
        normalized.split(
            "\n"
        );

    let currentParagraph = [];

    let currentField =
        null;

    function flushField() {

        if (!currentField) {
            return;
        }

        const fieldContainer =
            document.createElement(
                "div"
            );

        fieldContainer.className =
            "analysis-data";

        const fieldItem =
            document.createElement(
                "div"
            );

        fieldItem.className =
            "analysis-data-item";

        const label =
            document.createElement(
                "span"
            );

        label.textContent =
            formatAnalysisTitle(
                currentField.key
            );

        const output =
            document.createElement(
                "strong"
            );

        output.textContent =
            currentField.value
                .join(" ")
                .trim() || "—";

        fieldItem.appendChild(
            label
        );

        fieldItem.appendChild(
            output
        );

        fieldContainer.appendChild(
            fieldItem
        );

        container.appendChild(
            fieldContainer
        );

        currentField = null;
    }

    function flushParagraph() {

        if (
            !currentParagraph.length
        ) {
            return;
        }

        const paragraph =
            document.createElement(
                "p"
            );

        paragraph.textContent =
            currentParagraph
                .join(" ")
                .trim();

        if (
            paragraph.textContent
        ) {

            container.appendChild(
                paragraph
            );
        }

        currentParagraph = [];
    }

    lines.forEach(
        line => {

            const trimmed =
                line.trim();

            if (!trimmed) {

                flushField();
                flushParagraph();

                return;
            }

            const headingMatch =
                trimmed.match(
                    /^(#{1,6})\s+(.+)$/
                );

            if (headingMatch) {

                flushField();
                flushParagraph();

                const level =
                    headingMatch[1].length;

                const heading =
                    document.createElement(
                        `h${level}`
                    );

                if (
                    level >= 2
                ) {
                    heading.className =
                        "analysis-report-heading";
                }

                heading.textContent =
                    headingMatch[2]
                        .trim();

                container.appendChild(
                    heading
                );

                return;
            }

            const fieldMatch =
                trimmed.match(
                    /^([^:]{1,120}):\s*(.*)$/
                );

            if (fieldMatch) {

                flushParagraph();
                flushField();

                currentField = {
                    key:
                        fieldMatch[1]
                            .trim(),

                    value:
                        fieldMatch[2]
                            ? [
                                fieldMatch[2]
                                    .trim()
                            ]
                            : []
                };

                return;
            }

            if (currentField) {

                currentField.value.push(
                    trimmed
                );

                return;
            }

            currentParagraph.push(
                trimmed
            );
        }
    );

    flushField();
    flushParagraph();
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
                `ITEM ${String(
                    index + 1
                ).padStart(
                    2,
                    "0"
                )}`;

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

    const entries =
        Object.entries(
            object
        );

    if (!entries.length) {
        return;
    }

    const data =
        document.createElement(
            "div"
        );

    data.className =
        "analysis-data analysis-object";

    entries.forEach(
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

function extractEmbeddedJson(
    text
) {

    if (
        typeof text !== "string"
    ) {
        return null;
    }

    const normalized =
        text.trim();

    if (!normalized) {
        return null;
    }

    const firstObject =
        normalized.indexOf("{");

    const firstArray =
        normalized.indexOf("[");

    let start = -1;

    if (
        firstObject === -1
    ) {

        start =
            firstArray;

    } else if (
        firstArray === -1
    ) {

        start =
            firstObject;

    } else {

        start =
            Math.min(
                firstObject,
                firstArray
            );
    }

    if (start === -1) {
        return null;
    }

    const parsed =
        parseJsonPrefix(
            normalized.slice(start)
        );

    if (!parsed) {
        return null;
    }

    return {

        before:
            normalized
                .slice(
                    0,
                    start
                )
                .trim(),

        value:
            parsed.value,

        after:
            normalized
                .slice(
                    start + parsed.length
                )
                .trim()
    };
}

function parseJsonPrefix(
    text
) {

    if (
        !text ||
        (
            text[0] !== "{" &&
            text[0] !== "["
        )
    ) {
        return null;
    }

    const opening =
        text[0];

    const closing =
        opening === "{"
            ? "}"
            : "]";

    let depth = 0;
    let inString = false;
    let escaped = false;

    for (
        let index = 0;
        index < text.length;
        index++
    ) {

        const character =
            text[index];

        if (inString) {

            if (escaped) {

                escaped = false;

            } else if (
                character === "\\"
            ) {

                escaped = true;

            } else if (
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
            character === opening
        ) {

            depth++;

        } else if (
            character === closing
        ) {

            depth--;

            if (depth === 0) {

                const candidate =
                    text.slice(
                        0,
                        index + 1
                    );

                try {

                    return {

                        value:
                            JSON.parse(
                                candidate
                            ),

                        length:
                            index + 1
                    };

                } catch (error) {

                    return null;
                }
            }
        }
    }

    return null;
}

function createSourceReport(
    value
) {

    const sourceText =
        extractSourceText(
            value
        );

    if (!sourceText) {
        return null;
    }

    const details =
        document.createElement(
            "details"
        );

    details.className =
        "analysis-source";

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
        sourceText;

    details.appendChild(
        summary
    );

    details.appendChild(
        pre
    );

    return details;
}

function extractSourceText(
    value
) {

    if (
        typeof value === "string"
    ) {

        const match =
            value.match(
                /(?:^|\n)\s*(?:SOURCE REPORT|SOURCE|RAW REPORT)\s*:?\s*([\s\S]*)$/i
            );

        if (
            match &&
            match[1].trim()
        ) {
            return match[1].trim();
        }

        return null;
    }

    if (
        Array.isArray(value)
    ) {

        for (
            const item of value
        ) {

            const source =
                extractSourceText(
                    item
                );

            if (source) {
                return source;
            }
        }

        return null;
    }

    if (
        value &&
        typeof value === "object"
    ) {

        const sourceKeys = [
            "source_report",
            "sourceReport",
            "raw_report",
            "rawReport",
            "source"
        ];

        for (
            const key of sourceKeys
        ) {

            if (
                Object.prototype.hasOwnProperty.call(
                    value,
                    key
                )
            ) {

                const source =
                    value[key];

                if (
                    typeof source === "string" &&
                    source.trim()
                ) {

                    return source.trim();
                }

                if (
                    source &&
                    typeof source === "object"
                ) {

                    return JSON.stringify(
                        source,
                        null,
                        2
                    );
                }
            }
        }
    }

    return null;
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
            !Number.isFinite(value)
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

    if (
        regime !== "—"
    ) {

        description +=
            ` The current market regime is ${regime}.`;
    }

    if (
        timeframe !== "—"
    ) {

        description +=
            ` The published signal timeframe is ${timeframe}.`;
    }

    if (
        score !== "—"
    ) {

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

    if (
        !Number.isFinite(value)
    ) {
        return "—";
    }

    return `$${value.toFixed(4)}`;
}

function formatRiskReward(
    value
) {

    if (
        !Number.isFinite(value)
    ) {
        return "—";
    }

    return `${value.toFixed(2)}R`;
}

function formatScore(
    value
) {

    if (
        !Number.isFinite(value)
    ) {
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
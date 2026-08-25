"use strict";

const ANALYSIS_DATA_URL = "data/analysis_latest.json";

document.addEventListener(
    "DOMContentLoaded",
    initializeAnalysis
);

async function initializeAnalysis() {

    const ticker =
        getRequestedTicker();

    if (!ticker) {

        renderAnalysisFailure(
            "NO TICKER REQUESTED",
            "The page URL does not contain a ticker parameter.",
            "Expected URL format: ticker-profile.html?ticker=BCAB"
        );

        return;
    }

    showAnalysisLoading(
        ticker
    );

    try {

        const result =
            await loadAnalysisData(
                ticker
            );

        renderAnalysis(
            result
        );

    } catch (error) {

        console.error(
            "NEA28V1 analysis error:",
            error
        );

        renderAnalysisFailure(
            "ANALYSIS LOAD FAILURE",
            `Unable to load analysis data for ${ticker}.`,
            error.message
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

async function loadAnalysisData(
    ticker
) {

    const url =
        `${ANALYSIS_DATA_URL}?t=${Date.now()}`;

    let response;

    try {

        response =
            await fetch(
                url,
                {
                    cache: "no-store"
                }
            );

    } catch (error) {

        throw new Error(
            `NETWORK FAILURE: Unable to request ${ANALYSIS_DATA_URL}. ${error.message}`
        );
    }

    if (!response.ok) {

        throw new Error(
            `HTTP FAILURE: ${ANALYSIS_DATA_URL} returned HTTP ${response.status} ${response.statusText}.`
        );
    }

    let data;

    try {

        data =
            await response.json();

    } catch (error) {

        throw new Error(
            `JSON FAILURE: ${ANALYSIS_DATA_URL} was loaded but could not be parsed as JSON. ${error.message}`
        );
    }

    if (
        !data ||
        typeof data !== "object" ||
        Array.isArray(data)
    ) {

        throw new Error(
            `DATA FAILURE: ${ANALYSIS_DATA_URL} does not contain a valid JSON object.`
        );
    }

    if (
        !Object.prototype.hasOwnProperty.call(
            data,
            "tickers"
        )
    ) {

        throw new Error(
            `SCHEMA FAILURE: ${ANALYSIS_DATA_URL} does not contain the required "tickers" object.`
        );
    }

    if (
        !data.tickers ||
        typeof data.tickers !== "object" ||
        Array.isArray(data.tickers)
    ) {

        throw new Error(
            `SCHEMA FAILURE: "tickers" exists but is not a valid ticker index.`
        );
    }

    if (
        !Object.prototype.hasOwnProperty.call(
            data.tickers,
            ticker
        )
    ) {

        throw new Error(
            `TICKER FAILURE: ${ticker} does not exist in data.tickers. Available tickers: ${Object.keys(data.tickers).join(", ") || "NONE"}.`
        );
    }

    const tickerAnalysis =
        data.tickers[ticker];

    if (
        !tickerAnalysis ||
        typeof tickerAnalysis !== "object" ||
        Array.isArray(tickerAnalysis)
    ) {

        throw new Error(
            `TICKER DATA FAILURE: data.tickers.${ticker} is not a valid analysis object.`
        );
    }

    return {
        dataset: data,
        ticker: ticker,
        analysis: tickerAnalysis
    };
}

function renderAnalysis(
    result
) {

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

    if (container) {
        container.innerHTML = "";
    }

    hideAnalysisFailure();

    const analysis =
        result.analysis;

    renderAnalysisMetadata(
        analysis
    );

    renderAnalysisRisk(
        analysis
    );

    if (
        !Object.prototype.hasOwnProperty.call(
            analysis,
            "analysis_blocks"
        )
    ) {

        renderAnalysisFailure(
            "ANALYSIS BLOCK FAILURE",
            `Analysis data exists for ${result.ticker}, but no "analysis_blocks" property was published.`,
            `Available ticker fields: ${Object.keys(analysis).join(", ") || "NONE"}`
        );

        return;
    }

    const blocks =
        normalizeAnalysisBlocks(
            analysis.analysis_blocks
        );

    if (
        !blocks.length
    ) {

        renderAnalysisFailure(
            "ANALYSIS BLOCK FAILURE",
            `The ticker record for ${result.ticker} contains "analysis_blocks", but there are no renderable analysis blocks.`,
            `analysis_blocks type: ${Array.isArray(analysis.analysis_blocks) ? "array" : typeof analysis.analysis_blocks}`
        );

        return;
    }

    let renderedCount = 0;

    blocks.forEach(
        (
            block,
            index
        ) => {

            try {

                const rendered =
                    renderAnalysisBlock(
                        block.key,
                        block.value,
                        index
                    );

                if (rendered) {
                    renderedCount++;
                }

            } catch (error) {

                console.error(
                    `Unable to render analysis block "${block.key}".`,
                    error
                );

                renderAnalysisFailure(
                    "ANALYSIS BLOCK RENDER FAILURE",
                    `Analysis block "${block.key}" could not be rendered.`,
                    error.message
                );
            }
        }
    );

    if (
        renderedCount === 0
    ) {

        renderAnalysisFailure(
            "ANALYSIS RENDER FAILURE",
            `Analysis data was found for ${result.ticker}, but none of the ${blocks.length} analysis blocks produced visible HTML.`,
            `Blocks discovered: ${blocks.map(block => block.key).join(", ")}`
        );

        return;
    }

    if (emptyState) {

        emptyState.classList.add(
            "hidden"
        );
    }

    if (section) {

        section.classList.remove(
            "hidden"
        );
    }

    console.info(
        `NEA28V1: rendered ${renderedCount} analysis blocks for ${result.ticker}.`
    );
}

function normalizeAnalysisBlocks(
    blocks
) {

    if (
        !blocks ||
        typeof blocks !== "object" ||
        Array.isArray(blocks)
    ) {
        return [];
    }

    return Object.entries(
        blocks
    )
        .filter(
            (
                [key, value]
            ) => {

                if (
                    !String(key).trim()
                ) {
                    return false;
                }

                if (
                    value === null ||
                    value === undefined
                ) {
                    return false;
                }

                if (
                    typeof value === "string" &&
                    !value.trim()
                ) {
                    return false;
                }

                return true;
            }
        )
        .map(
            (
                [key, value]
            ) => ({
                key:
                    String(key),
                value
            })
        );
}

function renderAnalysisBlock(
    key,
    value,
    index
) {

    const container =
        document.getElementById(
            "analysisBlocks"
        );

    if (!container) {

        throw new Error(
            'HTML FAILURE: element id="analysisBlocks" was not found.'
        );
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

    return true;
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

            if (
                jsonContainer.childNodes.length
            ) {

                container.appendChild(
                    jsonContainer
                );
            }

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

    if (
        value === null ||
        value === undefined ||
        value === ""
    ) {

        const paragraph =
            document.createElement(
                "p"
            );

        paragraph.textContent =
            "VALUE: No value was supplied by the analysis engine.";

        container.appendChild(
            paragraph
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
    let currentField = null;

    function flushField() {

        if (!currentField) {
            return;
        }

        const fieldValue =
            currentField.value
                .join(" ")
                .trim();

        if (!fieldValue) {

            currentField = null;
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
            fieldValue;

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
                    Math.min(
                        headingMatch[1].length,
                        6
                    );

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

    if (
        !Array.isArray(items) ||
        !items.length
    ) {

        const paragraph =
            document.createElement(
                "p"
            );

        paragraph.textContent =
            "ARRAY: Analysis returned an empty array.";

        container.appendChild(
            paragraph
        );

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

    if (
        !object ||
        typeof object !== "object" ||
        Array.isArray(object)
    ) {

        return;
    }

    const entries =
        Object.entries(
            object
        );

    if (!entries.length) {

        const paragraph =
            document.createElement(
                "p"
            );

        paragraph.textContent =
            "OBJECT: Analysis returned an empty object.";

        container.appendChild(
            paragraph
        );

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

function showAnalysisLoading(
    ticker
) {

    const section =
        document.getElementById(
            "analysisSection"
        );

    const emptyState =
        document.getElementById(
            "analysisEmpty"
        );

    if (section) {

        section.classList.remove(
            "hidden"
        );
    }

    if (emptyState) {

        emptyState.classList.add(
            "hidden"
        );
    }

    const container =
        document.getElementById(
            "analysisBlocks"
        );

    if (container) {

        container.innerHTML = "";

        const message =
            document.createElement(
                "p"
            );

        message.className =
            "analysis-loading";

        message.textContent =
            `Loading analysis data for ${ticker}…`;

        container.appendChild(
            message
        );
    }
}

function renderAnalysisFailure(
    title,
    message,
    detail
) {

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

    if (emptyState) {

        emptyState.classList.add(
            "hidden"
        );
    }

    if (section) {

        section.classList.remove(
            "hidden"
        );
    }

    if (!container) {
        return;
    }

    container.innerHTML = "";

    const diagnostic =
        document.createElement(
            "article"
        );

    diagnostic.className =
        "analysis-card analysis-diagnostic";

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
        "ERR";

    const heading =
        document.createElement(
            "h3"
        );

    heading.textContent =
        title;

    header.appendChild(
        indexLabel
    );

    header.appendChild(
        heading
    );

    const content =
        document.createElement(
            "div"
        );

    content.className =
        "analysis-card-content";

    const primary =
        document.createElement(
            "p"
        );

    primary.textContent =
        message;

    content.appendChild(
        primary
    );

    if (detail) {

        const details =
            document.createElement(
                "pre"
            );

        details.className =
            "analysis-diagnostic-detail";

        details.textContent =
            detail;

        content.appendChild(
            details
        );
    }

    diagnostic.appendChild(
        header
    );

    diagnostic.appendChild(
        content
    );

    container.appendChild(
        diagnostic
    );

    console.error(
        title,
        message,
        detail
    );
}

function hideAnalysisFailure() {

    const container =
        document.getElementById(
            "analysisBlocks"
        );

    if (!container) {
        return;
    }

    const failures =
        container.querySelectorAll(
            ".analysis-diagnostic"
        );

    failures.forEach(
        failure =>
            failure.remove()
    );
}

function resetAnalysis() {

    const container =
        document.getElementById(
            "analysisBlocks"
        );

    if (container) {
        container.innerHTML = "";
    }

    renderAnalysisMetadata(
        null
    );

    renderAnalysisRisk(
        null
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
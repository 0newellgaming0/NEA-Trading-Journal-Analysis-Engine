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
            "NO TICKER SPECIFIED",
            "The analysis page was loaded without a ticker parameter.",
            "Expected URL format: ticker-profile.html?ticker=BCAB"
        );

        return;
    }

    try {

        const result =
            await loadAnalysisData(
                ticker
            );

        if (
            result &&
            result.type === "success"
        ) {

            renderAnalysis(
                result.analysis,
                ticker,
                result.data
            );

            return;
        }

        renderAnalysisLoadDiagnostic(
            result,
            ticker
        );

    } catch (error) {

        console.error(
            "NEA28V1 analysis error:",
            error
        );

        renderAnalysisFailure(
            "ANALYSIS LOAD FAILURE",
            `Unable to load analysis data for ${ticker}.`,
            error instanceof Error
                ? error.message
                : String(error)
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

    const requestUrl =
        `${ANALYSIS_DATA_URL}?t=${Date.now()}`;

    let response;

    try {

        response =
            await fetch(
                requestUrl,
                {
                    cache: "no-store"
                }
            );

    } catch (error) {

        return {
            type:
                "network_error",

            ticker,

            url:
                ANALYSIS_DATA_URL,

            message:
                error instanceof Error
                    ? error.message
                    : String(error)
        };
    }

    if (!response.ok) {

        return {
            type:
                "http_error",

            ticker,

            url:
                ANALYSIS_DATA_URL,

            status:
                response.status,

            statusText:
                response.statusText || "",

            message:
                `${ANALYSIS_DATA_URL} returned HTTP ${response.status} ${response.statusText || ""}.`
                    .trim()
        };
    }

    let data;

    try {

        data =
            await response.json();

    } catch (error) {

        return {
            type:
                "json_error",

            ticker,

            url:
                ANALYSIS_DATA_URL,

            message:
                error instanceof Error
                    ? error.message
                    : String(error)
        };
    }

    if (
        !data ||
        typeof data !== "object" ||
        Array.isArray(data)
    ) {

        return {
            type:
                "invalid_dataset",

            ticker,

            url:
                ANALYSIS_DATA_URL,

            message:
                "The JSON response is not a valid object."
        };
    }

    if (
        !Object.prototype.hasOwnProperty.call(
            data,
            "tickers"
        )
    ) {

        return {
            type:
                "missing_tickers",

            ticker,

            url:
                ANALYSIS_DATA_URL,

            data,

            message:
                'The JSON dataset does not contain the required "tickers" property.'
        };
    }

    const tickerIndex =
        data.tickers;

    if (
        !tickerIndex ||
        typeof tickerIndex !== "object" ||
        Array.isArray(tickerIndex)
    ) {

        return {
            type:
                "invalid_tickers",

            ticker,

            url:
                ANALYSIS_DATA_URL,

            data,

            message:
                'The JSON "tickers" property is not a valid ticker index.'
        };
    }

    if (
        !Object.prototype.hasOwnProperty.call(
            tickerIndex,
            ticker
        )
    ) {

        return {
            type:
                "ticker_not_found",

            ticker,

            url:
                ANALYSIS_DATA_URL,

            data,

            availableTickers:
                Object.keys(
                    tickerIndex
                ),

            message:
                `No analysis entry exists for ticker ${ticker}.`
        };
    }

    const tickerAnalysis =
        tickerIndex[ticker];

    if (
        !tickerAnalysis ||
        typeof tickerAnalysis !== "object" ||
        Array.isArray(tickerAnalysis)
    ) {

        return {
            type:
                "invalid_ticker_record",

            ticker,

            url:
                ANALYSIS_DATA_URL,

            data,

            message:
                `The ${ticker} record exists but is not a valid object.`
        };
    }

    return {
        type:
            "success",

        ticker,

        data,

        analysis:
            tickerAnalysis
    };
}

function renderAnalysis(
    analysis,
    ticker,
    dataset
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

    renderAnalysisMetadata(
        analysis
    );

    renderAnalysisRisk(
        analysis
    );

    if (
        !analysis ||
        typeof analysis !== "object" ||
        Array.isArray(analysis)
    ) {

        renderAnalysisFailure(
            "INVALID TICKER RECORD",
            `The ${ticker} ticker record was found but could not be rendered.`,
            "The ticker record is not a valid JSON object."
        );

        return;
    }

    const blocksPropertyExists =
        Object.prototype.hasOwnProperty.call(
            analysis,
            "analysis_blocks"
        );

    if (!blocksPropertyExists) {

        renderAnalysisFailure(
            "ANALYSIS BLOCKS MISSING",
            `The ${ticker} record was loaded successfully, but it does not contain "analysis_blocks".`,
            `Available ticker fields: ${Object.keys(analysis).join(", ") || "none"}`
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

        return;
    }

    const blocks =
        normalizeAnalysisBlocks(
            analysis.analysis_blocks
        );

    if (!blocks.length) {

        renderAnalysisFailure(
            "NO ANALYSIS BLOCKS",
            `The ${ticker} record was loaded successfully, but "analysis_blocks" contains no renderable entries.`,
            describeAnalysisBlocks(
                analysis.analysis_blocks
            )
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

        return;
    }

    let renderedCount = 0;
    let failedCount = 0;

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

                } else {

                    failedCount++;

                    renderAnalysisBlockDiagnostic(
                        block.key,
                        "The block existed but produced no visible HTML content."
                    );
                }

            } catch (error) {

                failedCount++;

                console.error(
                    `Unable to render analysis block "${block.key}".`,
                    error
                );

                renderAnalysisBlockDiagnostic(
                    block.key,
                    error instanceof Error
                        ? error.message
                        : String(error)
                );
            }
        }
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

    if (
        renderedCount === 0 &&
        failedCount > 0
    ) {

        renderAnalysisFailure(
            "ANALYSIS RENDER FAILURE",
            `The ${ticker} analysis data was loaded, but none of the ${blocks.length} analysis blocks could be rendered.`,
            `Rendered: 0 | Failed: ${failedCount}`
        );

        return;
    }

    if (
        failedCount > 0
    ) {

        renderAnalysisDiagnosticNotice(
            `${renderedCount} analysis block${renderedCount === 1 ? "" : "s"} rendered successfully. ${failedCount} block${failedCount === 1 ? "" : "s"} failed and were individually diagnosed below.`
        );
    }

    if (
        dataset &&
        dataset.generated_at
    ) {

        renderDatasetGenerationMetadata(
            dataset.generated_at
        );
    }
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
            'Required HTML element "#analysisBlocks" was not found.'
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
        String(
            index + 1
        ).padStart(
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

function renderAnalysisBlockDiagnostic(
    key,
    message
) {

    const container =
        document.getElementById(
            "analysisBlocks"
        );

    if (!container) {
        return;
    }

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

    const title =
        document.createElement(
            "h3"
        );

    title.textContent =
        `ANALYSIS BLOCK FAILURE: ${formatAnalysisTitle(key)}`;

    header.appendChild(
        title
    );

    const content =
        document.createElement(
            "div"
        );

    content.className =
        "analysis-card-content"
    ;

    const messageElement =
        document.createElement(
            "p"
        );

    messageElement.textContent =
        message;

    content.appendChild(
        messageElement
    );

    diagnostic.appendChild(
        header
    );

    diagnostic.appendChild(
        content
    );

    container.appendChild(
        diagnostic
    );
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
            "No value supplied.";

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

        const paragraph =
            document.createElement(
                "p"
            );

        paragraph.textContent =
            "No analysis text supplied.";

        container.appendChild(
            paragraph
        );

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
            "Analysis returned an empty list.";

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
            "Analysis returned an empty object.";

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
        normalized.indexOf(
            "{"
        );

    const firstArray =
        normalized.indexOf(
            "["
        );

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
            normalized.slice(
                start
            )
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
            !Number.isFinite(
                value
            )
        ) {

            return "—";
        }

        return String(
            value
        );
    }

    return String(
        value
    );
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

function renderAnalysisLoadDiagnostic(
    result,
    ticker
) {

    if (!result) {

        renderAnalysisFailure(
            "ANALYSIS LOAD FAILURE",
            `Unable to load analysis data for ${ticker}.`,
            "No diagnostic result was returned."
        );

        return;
    }

    switch (
        result.type
    ) {

        case "http_error":

            renderAnalysisFailure(
                "ANALYSIS LOAD FAILURE",
                `Unable to load analysis data for ${ticker}.`,
                `HTTP FAILURE: ${result.url} returned HTTP ${result.status} ${result.statusText}.`
            );

            return;

        case "network_error":

            renderAnalysisFailure(
                "ANALYSIS NETWORK FAILURE",
                `The browser could not retrieve analysis data for ${ticker}.`,
                `NETWORK ERROR: ${result.message}`
            );

            return;

        case "json_error":

            renderAnalysisFailure(
                "ANALYSIS JSON FAILURE",
                `The analysis file was reached, but its contents could not be parsed as JSON.`,
                `JSON PARSE ERROR: ${result.message}`
            );

            return;

        case "invalid_dataset":

        case "missing_tickers":

        case "invalid_tickers":

            renderAnalysisFailure(
                "ANALYSIS DATASET FAILURE",
                `The analysis file was loaded but does not match the required dataset structure.`,
                result.message
            );

            return;

        case "ticker_not_found":

            renderAnalysisFailure(
                "TICKER ANALYSIS NOT FOUND",
                `The analysis dataset loaded successfully, but no record exists for ${ticker}.`,
                result.availableTickers &&
                result.availableTickers.length
                    ? `Available tickers: ${result.availableTickers.join(", ")}`
                    : "The ticker index contains no ticker records."
            );

            return;

        case "invalid_ticker_record":

            renderAnalysisFailure(
                "INVALID TICKER RECORD",
                `The ${ticker} entry exists in the dataset but is not renderable.`,
                result.message
            );

            return;

        default:

            renderAnalysisFailure(
                "ANALYSIS LOAD FAILURE",
                `Unable to load analysis data for ${ticker}.`,
                result.message ||
                    "Unknown analysis loading failure."
            );
    }
}

function renderAnalysisFailure(
    title,
    message,
    diagnostic
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

    if (!container) {
        return;
    }

    container.innerHTML = "";

    const card =
        document.createElement(
            "article"
        );

    card.className =
        "analysis-card analysis-diagnostic analysis-load-failure";

    const header =
        document.createElement(
            "div"
        );

    header.className =
        "analysis-card-header";

    const heading =
        document.createElement(
            "h3"
        );

    heading.textContent =
        title;

    header.appendChild(
        heading
    );

    const content =
        document.createElement(
            "div"
        );

    content.className =
        "analysis-card-content";

    const messageElement =
        document.createElement(
            "p"
        );

    messageElement.textContent =
        message;

    content.appendChild(
        messageElement
    );

    if (diagnostic) {

        const diagnosticBlock =
            document.createElement(
                "pre"
            );

        diagnosticBlock.className =
            "analysis-diagnostic-detail";

        diagnosticBlock.textContent =
            diagnostic;

        content.appendChild(
            diagnosticBlock
        );
    }

    card.appendChild(
        header
    );

    card.appendChild(
        content
    );

    container.appendChild(
        card
    );
}

function renderAnalysisDiagnosticNotice(
    message
) {

    const container =
        document.getElementById(
            "analysisBlocks"
        );

    if (!container) {
        return;
    }

    const notice =
        document.createElement(
            "div"
        );

    notice.className =
        "analysis-diagnostic-notice";

    notice.textContent =
        message;

    container.insertBefore(
        notice,
        container.firstChild
    );
}

function renderAnalysisBlockDiagnostic(
    key,
    message
) {

    const container =
        document.getElementById(
            "analysisBlocks"
        );

    if (!container) {
        return;
    }

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

    const title =
        document.createElement(
            "h3"
        );

    title.textContent =
        `ANALYSIS BLOCK FAILURE: ${formatAnalysisTitle(key)}`;

    header.appendChild(
        title
    );

    const content =
        document.createElement(
            "div"
        );

    content.className =
        "analysis-card-content";

    const messageElement =
        document.createElement(
            "p"
        );

    messageElement.textContent =
        message;

    content.appendChild(
        messageElement
    );

    diagnostic.appendChild(
        header
    );

    diagnostic.appendChild(
        content
    );

    container.appendChild(
        diagnostic
    );
}

function describeAnalysisBlocks(
    blocks
) {

    if (
        blocks === null ||
        blocks === undefined
    ) {

        return "analysis_blocks is null or undefined.";
    }

    if (
        Array.isArray(blocks)
    ) {

        return `analysis_blocks is an array containing ${blocks.length} entries. Expected an object keyed by analysis block name.`;
    }

    if (
        typeof blocks !== "object"
    ) {

        return `analysis_blocks has type "${typeof blocks}". Expected an object keyed by analysis block name.`;
    }

    const keys =
        Object.keys(
            blocks
        );

    return keys.length
        ? `analysis_blocks contains ${keys.length} key(s): ${keys.join(", ")}`
        : "analysis_blocks is an empty object.";
}

function renderDatasetGenerationMetadata(
    generatedAt
) {

    const existing =
        document.getElementById(
            "analysisDatasetGeneratedAt"
        );

    if (!existing) {
        return;
    }

    existing.textContent =
        formatTimestamp(
            generatedAt
        );
}

function hideAnalysisFailure() {

    const existing =
        document.querySelectorAll(
            ".analysis-load-failure"
        );

    existing.forEach(
        element => {
            element.remove();
        }
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

    renderAnalysisFailure(
        "ANALYSIS UNAVAILABLE",
        "No ticker was supplied for the analysis page.",
        "Provide a ticker query parameter."
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
        new Date(
            value
        );

    if (
        Number.isNaN(
            date.getTime()
        )
    ) {

        return String(
            value
        );
    }

    return date.toLocaleString(
        "en-US",
        {
            month:
                "short",

            day:
                "numeric",

            year:
                "numeric",

            hour:
                "numeric",

            minute:
                "2-digit"
        }
    );
}
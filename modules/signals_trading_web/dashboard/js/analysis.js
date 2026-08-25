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

        renderAnalysisDiagnostic(
            "NO TICKER REQUESTED",
            "The page URL does not contain a ticker parameter.",
            "Expected URL format: ticker-profile.html?ticker=BCAB"
        );

        return;
    }

    renderAnalysisLoading(
        ticker
    );

    try {

        const publication =
            await loadAnalysisData(
                ticker
            );

        renderAnalysis(
            publication
        );

    } catch (error) {

        console.error(
            "NEA28V1 analysis error:",
            error
        );

        renderAnalysisLoadFailure(
            ticker,
            error
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

    let response;

    try {

        response =
            await fetch(
                `${ANALYSIS_DATA_URL}?t=${Date.now()}`,
                {
                    cache: "no-store"
                }
            );

    } catch (error) {

        throw new Error(
            `NETWORK FAILURE: Unable to fetch ${ANALYSIS_DATA_URL}. ${error.message}`
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
            `JSON PARSE FAILURE: ${ANALYSIS_DATA_URL} does not contain valid JSON. ${error.message}`
        );
    }

    if (
        !data ||
        typeof data !== "object" ||
        Array.isArray(data)
    ) {

        throw new Error(
            "DATASET STRUCTURE FAILURE: The analysis publication root is not a valid JSON object."
        );
    }

    const publicationSchemaVersion =
        data.schema_version;

    const publicationGeneratedAt =
        data.generated_at;

    const tickerIndex =
        data.tickers;

    if (
        !tickerIndex ||
        typeof tickerIndex !== "object" ||
        Array.isArray(tickerIndex)
    ) {

        throw new Error(
            'DATASET STRUCTURE FAILURE: The publication does not contain a valid "tickers" object.'
        );
    }

    if (
        !Object.prototype.hasOwnProperty.call(
            tickerIndex,
            ticker
        )
    ) {

        throw new Error(
            `TICKER NOT FOUND: ${ticker} does not exist in data.tickers.`
        );
    }

    const tickerAnalysis =
        tickerIndex[ticker];

    if (
        !tickerAnalysis ||
        typeof tickerAnalysis !== "object" ||
        Array.isArray(tickerAnalysis)
    ) {

        throw new Error(
            `TICKER RECORD FAILURE: data.tickers.${ticker} exists but is not a valid object.`
        );
    }

    return {

        ticker,

        schema_version:
            publicationSchemaVersion,

        generated_at:
            publicationGeneratedAt,

        analysis:
            tickerAnalysis
    };
}

function renderAnalysis(
    publication
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

    if (
        !publication ||
        typeof publication !== "object"
    ) {

        renderAnalysisDiagnostic(
            "INVALID PUBLICATION",
            "The analysis publication could not be interpreted.",
            "The JavaScript received no valid publication object."
        );

        return;
    }

    const analysis =
        publication.analysis;

    if (
        !analysis ||
        typeof analysis !== "object" ||
        Array.isArray(analysis)
    ) {

        renderAnalysisDiagnostic(
            "INVALID TICKER ANALYSIS",
            `The ticker record for ${publication.ticker} exists, but its analysis record is invalid.`,
            `data.tickers.${publication.ticker} must contain an object.`
        );

        return;
    }

    renderPublicationMetadata(
        publication
    );

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

        renderAnalysisDiagnostic(
            "ANALYSIS BLOCKS MISSING",
            `${publication.ticker} exists in the publication, but no analysis_blocks field was provided.`,
            `The ticker record contains ${Object.keys(analysis).length} field(s), but analysis_blocks is absent.`
        );

        return;
    }

    const rawBlocks =
        analysis.analysis_blocks;

    if (
        rawBlocks === null ||
        rawBlocks === undefined
    ) {

        renderAnalysisDiagnostic(
            "ANALYSIS BLOCKS ARE NULL",
            `${publication.ticker} contains analysis_blocks, but its value is null or undefined.`,
            "The publisher created the field but did not provide analysis content."
        );

        return;
    }

    if (
        typeof rawBlocks !== "object" ||
        Array.isArray(rawBlocks)
    ) {

        renderAnalysisDiagnostic(
            "INVALID ANALYSIS BLOCK STRUCTURE",
            `${publication.ticker} contains analysis_blocks, but the field is not a JSON object.`,
            `Received type: ${Array.isArray(rawBlocks) ? "array" : typeof rawBlocks}.`
        );

        return;
    }

    const blocks =
        normalizeAnalysisBlocks(
            rawBlocks
        );

    if (!blocks.length) {

        renderAnalysisDiagnostic(
            "NO ANALYSIS BLOCKS",
            `${publication.ticker} contains an analysis_blocks object, but it contains no publishable entries.`,
            `analysis_blocks contains ${Object.keys(rawBlocks).length} raw field(s). Empty, null, undefined, and blank values are excluded from rendering.`
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

    const diagnostics = [];
    let renderedCount = 0;

    blocks.forEach(
        (
            block,
            index
        ) => {

            try {

                const result =
                    renderAnalysisBlock(
                        block.key,
                        block.value,
                        index
                    );

                if (result) {

                    renderedCount++;

                } else {

                    diagnostics.push(
                        `${block.key}: renderer returned no result.`
                    );
                }

            } catch (error) {

                console.error(
                    `Unable to render analysis block "${block.key}".`,
                    error
                );

                diagnostics.push(
                    `${block.key}: ${error.message}`
                );

                renderAnalysisBlockFailure(
                    block.key,
                    error,
                    index
                );
            }
        }
    );

    if (
        renderedCount === 0
    ) {

        renderAnalysisDiagnostic(
            "ANALYSIS RENDERING FAILURE",
            `${publication.ticker} contains ${blocks.length} published analysis block(s), but none completed normal rendering.`,
            diagnostics.length
                ? diagnostics.join(" | ")
                : "No additional renderer diagnostics were returned."
        );

        return;
    }

    if (diagnostics.length) {

        renderAnalysisDiagnostic(
            "PARTIAL ANALYSIS RENDER",
            `${renderedCount} of ${blocks.length} published analysis block(s) rendered normally.`,
            diagnostics.join(" | "),
            true
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

                if (
                    typeof value === "string" &&
                    !value.trim()
                ) {
                    return false;
                }

                if (
                    Array.isArray(value) &&
                    value.length === 0
                ) {
                    return false;
                }

                if (
                    value &&
                    typeof value === "object" &&
                    !Array.isArray(value) &&
                    Object.keys(value).length === 0
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
            'HTML TARGET MISSING: element "#analysisBlocks" does not exist.'
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

    try {

        renderAnalysisValue(
            content,
            value
        );

    } catch (error) {

        renderRawAnalysisValue(
            content,
            value,
            `Renderer failure: ${error.message}`
        );
    }

    if (
        !content.childNodes.length
    ) {

        renderRawAnalysisValue(
            content,
            value,
            "The analysis block exists in JSON but its value could not be formatted by the normal renderer."
        );
    }

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

function renderAnalysisBlockFailure(
    key,
    error,
    index
) {

    const container =
        document.getElementById(
            "analysisBlocks"
        );

    if (!container) {
        return;
    }

    const card =
        document.createElement(
            "article"
        );

    card.className =
        "analysis-card analysis-render-error";

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

    const title =
        document.createElement(
            "h3"
        );

    title.textContent =
        formatAnalysisTitle(
            key
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

    const diagnostic =
        document.createElement(
            "p"
        );

    diagnostic.textContent =
        `ANALYSIS RENDERER FAILURE: ${error.message}`;

    content.appendChild(
        diagnostic
    );

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

function renderRawAnalysisValue(
    container,
    value,
    reason
) {

    if (reason) {

        const diagnostic =
            document.createElement(
                "p"
            );

        diagnostic.textContent =
            reason;

        container.appendChild(
            diagnostic
        );
    }

    const pre =
        document.createElement(
            "pre"
        );

    pre.textContent =
        serializeAnalysisValue(
            value
        );

    container.appendChild(
        pre
    );
}

function serializeAnalysisValue(
    value
) {

    if (
        typeof value === "string"
    ) {
        return value;
    }

    try {

        return JSON.stringify(
            value,
            null,
            2
        );

    } catch (error) {

        return String(
            value
        );
    }
}

function renderPublicationMetadata(
    publication
) {

    const existing =
        document.getElementById(
            "analysisPublicationMetadata"
        );

    if (existing) {
        existing.remove();
    }

    const section =
        document.getElementById(
            "analysisSection"
        );

    if (!section) {
        return;
    }

    const metadata =
        document.createElement(
            "div"
        );

    metadata.id =
        "analysisPublicationMetadata";

    metadata.className =
        "analysis-publication-metadata";

    const title =
        document.createElement(
            "h3"
        );

    title.textContent =
        "ANALYSIS PUBLICATION";

    metadata.appendChild(
        title
    );

    appendDiagnosticField(
        metadata,
        "Ticker",
        publication.ticker || "—"
    );

    appendDiagnosticField(
        metadata,
        "Schema Version",
        publication.schema_version === undefined
            ? "—"
            : String(
                publication.schema_version
            )
    );

    appendDiagnosticField(
        metadata,
        "Publication Generated",
        publication.generated_at
            ? formatTimestamp(
                publication.generated_at
            )
            : "—"
    );

    section.insertBefore(
        metadata,
        section.firstChild
    );
}

function appendDiagnosticField(
    container,
    label,
    value
) {

    const row =
        document.createElement(
            "div"
        );

    row.className =
        "analysis-data-item";

    const labelElement =
        document.createElement(
            "span"
        );

    labelElement.textContent =
        label;

    const valueElement =
        document.createElement(
            "strong"
        );

    valueElement.textContent =
        value;

    row.appendChild(
        labelElement
    );

    row.appendChild(
        valueElement
    );

    container.appendChild(
        row
    );
}

function renderAnalysisLoading(
    ticker
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

    if (container) {

        container.innerHTML = "";
    }

    if (emptyState) {

        emptyState.classList.remove(
            "hidden"
        );

        emptyState.textContent =
            `Loading analysis publication for ${ticker}...`;
    }
}

function renderAnalysisLoadFailure(
    ticker,
    error
) {

    renderAnalysisMetadata(
        null
    );

    renderAnalysisRisk(
        null
    );

    renderAnalysisDiagnostic(
        "ANALYSIS LOAD FAILURE",
        `Unable to load analysis data for ${ticker}.`,
        error && error.message
            ? error.message
            : "Unknown loading error."
    );
}

function renderAnalysisDiagnostic(
    title,
    message,
    detail,
    nonFatal = false
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

    if (container) {

        container.innerHTML = "";

        const card =
            document.createElement(
                "article"
            );

        card.className =
            nonFatal
                ? "analysis-card analysis-diagnostic"
                : "analysis-card analysis-error";

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

            details.textContent =
                detail;

            content.appendChild(
                details
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

    if (emptyState) {

        emptyState.classList.add(
            "hidden"
        );
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

            if (
                !container.childNodes.length
            ) {

                renderRawAnalysisValue(
                    container,
                    value
                );
            }

            return;
        }

        renderAnalysisText(
            container,
            value
        );

        if (
            !container.childNodes.length
        ) {

            renderRawAnalysisValue(
                container,
                value
            );
        }

        return;
    }

    if (
        Array.isArray(value)
    ) {

        renderAnalysisArray(
            container,
            value
        );

        if (
            !container.childNodes.length
        ) {

            renderRawAnalysisValue(
                container,
                value
            );
        }

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

        if (
            !container.childNodes.length
        ) {

            renderRawAnalysisValue(
                container,
                value
            );
        }

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
            "No value was supplied for this analysis block.";

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
        return;
    }

    const list =
        document.createElement(
            "div"
        );

    list.className =
        "analysis-list";

    let renderedCount = 0;

    items.forEach(
        (
            item,
            index
        ) => {

            if (
                item === null ||
                item === undefined ||
                item === ""
            ) {
                return;
            }

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

            const itemContent =
                document.createElement(
                    "div"
                );

            itemContent.className =
                "analysis-list-item-content";

            renderAnalysisValue(
                itemContent,
                item
            );

            if (
                itemContent.childNodes.length
            ) {

                itemElement.appendChild(
                    itemContent
                );

                list.appendChild(
                    itemElement
                );

                renderedCount++;
            }
        }
    );

    if (renderedCount) {

        container.appendChild(
            list
        );
    }
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
                    value === undefined ||
                    value === ""
                ) {
                    return false;
                }

                if (
                    Array.isArray(value) &&
                    !value.length
                ) {
                    return false;
                }

                if (
                    value &&
                    typeof value === "object" &&
                    !Array.isArray(value) &&
                    !Object.keys(value).length
                ) {
                    return false;
                }

                return true;
            }
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

                if (
                    nested.childNodes.length
                ) {

                    item.appendChild(
                        nested
                    );
                }

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

    if (
        data.childNodes.length
    ) {

        container.appendChild(
            data
        );
    }
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

    renderAnalysisDiagnostic(
        "ANALYSIS RESET",
        "No ticker analysis was requested.",
        "The page cannot select a ticker without a ticker query parameter."
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
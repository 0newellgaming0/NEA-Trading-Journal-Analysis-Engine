"use strict";

const TRADE_DATA_URL = "data/trades.json";
const TOP_PICK_COUNT = 10;

document.addEventListener(
    "DOMContentLoaded",
    initializeNewsletter
);

async function initializeNewsletter() {
    setPublicationDate();
    initializeBookmarkButton();

    try {
        const rawData = await loadTradeData();
        const trades = normalizeTradeData(rawData);

        if (!trades.length) {
            renderEmptyState();
            return;
        }

        const rankedTrades = rankTrades(trades);

        renderMarketBias(
            rawData,
            rankedTrades
        );

        renderMarketSummary(
            rawData,
            rankedTrades
        );

        renderMarketContext(
            rankedTrades
        );

        renderTopPicks(
            rankedTrades.slice(
                0,
                TOP_PICK_COUNT
            )
        );

        renderStockToWatch(
            rankedTrades
        );

    } catch (error) {
        console.error(
            "NEA28V1 newsletter error:",
            error
        );

        renderDataError();
    }
}


function initializeBookmarkButton() {
    const button =
        document.getElementById(
            "bookmarkPageButton"
        );

    if (!button) {
        return;
    }

    button.addEventListener(
        "click",
        bookmarkCurrentPage
    );
}


function bookmarkCurrentPage() {
    const title =
        document.title ||
        "NEA28V1 Daily Market Intelligence";

    const url =
        window.location.href;

    if (
        window.external &&
        typeof window.external.AddFavorite === "function"
    ) {
        try {
            window.external.AddFavorite(
                url,
                title
            );

            return;

        } catch (error) {
            console.warn(
                "Browser bookmark API unavailable:",
                error
            );
        }
    }

    showBookmarkInstructions();
}


function showBookmarkInstructions() {
    const button =
        document.getElementById(
            "bookmarkPageButton"
        );

    if (!button) {
        return;
    }

    const originalText =
        button.textContent;

    button.textContent =
        "PRESS CTRL+D TO BOOKMARK";

    button.classList.add(
        "bookmark-active"
    );

    setTimeout(() => {

        button.textContent =
            originalText;

        button.classList.remove(
            "bookmark-active"
        );

    }, 4000);
}


async function loadTradeData() {
    const response = await fetch(
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

    const ticker = firstValue(
        trade.ticker,
        trade.symbol,
        trade.Ticker,
        trade.Symbol
    );

    if (!ticker) {
        return null;
    }

    const entry = numericValue(
        firstValue(
            trade.entry,
            trade.entry_price,
            trade.Entry
        )
    );

    const stop = numericValue(
        firstValue(
            trade.stop,
            trade.stop_loss,
            trade.Stop
        )
    );

    const target = numericValue(
        firstValue(
            trade.target,
            trade.target_price,
            trade.Target
        )
    );

    const score = numericValue(
        firstValue(
            trade.score,
            trade.rank_score,
            trade.Score
        )
    );

    return {
        ticker:
            String(ticker).toUpperCase(),

        direction: firstValue(
            trade.direction,
            trade.side,
            trade.Direction
        ) || "—",

        setup: firstValue(
            trade.setup,
            trade.setup_type,
            trade.Setup
        ) || "Trade Setup",

        entry,
        stop,
        target,
        score,

        status: firstValue(
            trade.status,
            trade.Status
        ) || "—",

        raw: trade
    };
}


function rankTrades(trades) {
    return [...trades].sort((a, b) => {

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
    });
}


function renderMarketBias(
    rawData,
    trades
) {
    const bias =
        getMarketBias(
            rawData,
            trades
        );

    setText(
        "marketBias",
        bias.value
    );

    setText(
        "marketBiasDescription",
        bias.description
    );

    setText(
        "activeTradeCount",
        trades.length
    );

    const scores =
        trades
            .map(
                trade => trade.score
            )
            .filter(
                Number.isFinite
            );

    if (scores.length) {
        setText(
            "highestScore",
            formatScore(
                Math.max(...scores)
            )
        );
    }
}


function getMarketBias(
    rawData,
    trades
) {
    const explicitBias =
        firstValue(
            rawData.marketBias,
            rawData.market_bias,
            rawData.bias,
            rawData.market?.bias,
            rawData.market?.marketBias
        );

    if (explicitBias) {
        return {
            value:
                String(explicitBias),

            description:
                "Current market bias supplied by the NEA28V1 publication dataset."
        };
    }

    let longCount = 0;
    let shortCount = 0;

    trades.forEach(trade => {

        const direction =
            String(
                trade.direction
            ).toLowerCase();

        if (
            direction.includes("long") ||
            direction.includes("bull") ||
            direction.includes("buy")
        ) {
            longCount++;
        }

        if (
            direction.includes("short") ||
            direction.includes("bear") ||
            direction.includes("sell")
        ) {
            shortCount++;
        }
    });

    if (longCount > shortCount) {
        return {
            value: "Bullish",

            description:
                `${longCount} bullish opportunities currently exceed ` +
                `${shortCount} bearish opportunities in the published dataset.`
        };
    }

    if (shortCount > longCount) {
        return {
            value: "Bearish",

            description:
                `${shortCount} bearish opportunities currently exceed ` +
                `${longCount} bullish opportunities in the published dataset.`
        };
    }

    return {
        value: "Neutral",

        description:
            "Bullish and bearish qualifying opportunities are currently balanced."
    };
}


function renderMarketSummary(
    rawData,
    trades
) {
    const explicitSummary =
        firstValue(
            rawData.marketSummary,
            rawData.market_summary,
            rawData.summary,
            rawData.market?.summary
        );

    if (explicitSummary) {
        setText(
            "marketSummary",
            explicitSummary
        );

        return;
    }

    if (!trades.length) {
        return;
    }

    const highest =
        trades[0];

    setText(
        "marketSummary",
        `NEA28V1 currently identifies ${trades.length} ` +
        `qualifying trade opportunities. The highest-ranked ` +
        `published opportunity is ${highest.ticker} with a ` +
        `score of ${formatScore(highest.score)}.`
    );
}


function renderMarketContext(
    trades
) {
    const longCount =
        trades.filter(
            trade =>
                isLong(
                    trade.direction
                )
        ).length;

    const shortCount =
        trades.filter(
            trade =>
                isShort(
                    trade.direction
                )
        ).length;

    let directional;

    if (longCount > shortCount) {
        directional =
            "Bullish-Leaning";

    } else if (shortCount > longCount) {
        directional =
            "Bearish-Leaning";

    } else {
        directional =
            "Balanced";
    }

    setText(
        "directionalEnvironment",
        directional
    );

    setText(
        "directionalDescription",
        `${longCount} bullish and ${shortCount} bearish ` +
        `opportunities are currently represented.`
    );

    const setupCounts = {};

    trades.forEach(trade => {

        const setup =
            trade.setup ||
            "Unclassified";

        setupCounts[setup] =
            (setupCounts[setup] || 0) + 1;
    });

    const dominantSetup =
        Object.entries(
            setupCounts
        )
        .sort(
            (a, b) =>
                b[1] - a[1]
        )[0];

    if (dominantSetup) {

        setText(
            "setupEnvironment",
            dominantSetup[0]
        );

        setText(
            "setupDescription",
            `${dominantSetup[1]} published opportunities ` +
            `currently use this setup classification.`
        );
    }

    setText(
        "rankingEnvironment",
        "Active"
    );

    setText(
        "rankingDescription",
        "Published opportunities are ordered by available NEA28V1 score."
    );

    const structuredCount =
        trades.filter(
            trade =>
                Number.isFinite(
                    trade.entry
                ) &&
                Number.isFinite(
                    trade.stop
                ) &&
                Number.isFinite(
                    trade.target
                )
        ).length;

    setText(
        "riskEnvironment",
        `${structuredCount}/${trades.length} Structured`
    );

    setText(
        "riskDescription",
        `${structuredCount} opportunities currently contain ` +
        `entry, stop, and target values suitable for risk/reward evaluation.`
    );
}


function renderTopPicks(
    trades
) {
    const container =
        document.getElementById(
            "topPicks"
        );

    if (!container) {
        return;
    }

    if (!trades.length) {
        container.innerHTML =
            `<div class="loading">
                No qualifying trade opportunities are currently available.
             </div>`;

        return;
    }

    container.innerHTML =
        trades
            .map(
                (trade, index) =>
                    createTradeCard(
                        trade,
                        index + 1
                    )
            )
            .join("");
}


function createTradeCard(
    trade,
    rank
) {
    const rr =
        calculateRiskReward(
            trade.entry,
            trade.stop,
            trade.target,
            trade.direction
        );

    const ticker =
        escapeHtml(
            trade.ticker
        );

    const tickerProfileUrl =
        `ticker-profile.html?ticker=${encodeURIComponent(
            trade.ticker
        )}`;

    return `
        <article class="trade-card">

            <div class="trade-header">

                <div class="trade-rank">
                    RANK #${rank}
                </div>

                <div class="trade-ticker">

                    <a
                        href="${tickerProfileUrl}"
                        class="ticker-link"
                        aria-label="View ${ticker} ticker profile"
                    >
                        ${ticker}
                    </a>

                </div>

                <div class="trade-setup">
                    ${escapeHtml(trade.direction)}
                    &bull;
                    ${escapeHtml(trade.setup)}
                </div>

            </div>

            <div class="trade-body">

                <div class="trade-levels">

                    ${createLevel(
                        "ENTRY",
                        formatPrice(
                            trade.entry
                        )
                    )}

                    ${createLevel(
                        "STOP",
                        formatPrice(
                            trade.stop
                        )
                    )}

                    ${createLevel(
                        "TARGET",
                        formatPrice(
                            trade.target
                        )
                    )}

                    ${createLevel(
                        "SCORE",
                        formatScore(
                            trade.score
                        )
                    )}

                </div>

                <div class="trade-description">

                    <strong>
                        Setup:
                    </strong>

                    ${escapeHtml(
                        buildTradeDescription(
                            trade
                        )
                    )}

                </div>

                <div class="trade-metrics">

                    ${createMetric(
                        "RISK / REWARD",
                        formatRiskReward(rr)
                    )}

                    ${createMetric(
                        "DIRECTION",
                        trade.direction
                    )}

                    ${createMetric(
                        "SETUP",
                        trade.setup
                    )}

                    ${createMetric(
                        "STATUS",
                        trade.status
                    )}

                </div>

                <div class="trade-actions">

                    <a
                        href="${tickerProfileUrl}"
                        class="ticker-profile-button"
                    >
                        VIEW ${ticker} TICKER PROFILE →
                    </a>

                </div>

            </div>

        </article>
    `;
}


function createLevel(
    label,
    value
) {
    return `
        <div class="level">
            <span>
                ${escapeHtml(label)}
            </span>

            <strong>
                ${escapeHtml(value)}
            </strong>
        </div>
    `;
}


function createMetric(
    label,
    value
) {
    return `
        <div class="metric">
            <span>
                ${escapeHtml(label)}
            </span>

            <strong>
                ${escapeHtml(value)}
            </strong>
        </div>
    `;
}


function renderStockToWatch(
    trades
) {
    const container =
        document.getElementById(
            "stockToWatch"
        );

    if (!container) {
        return;
    }

    const candidate =
        findStockToWatch(
            trades
        );

    if (!candidate) {
        container.innerHTML =
            `<div class="loading">
                No developing opportunity is currently available.
             </div>`;

        return;
    }

    const rr =
        calculateRiskReward(
            candidate.entry,
            candidate.stop,
            candidate.target,
            candidate.direction
        );

    const candidateTicker =
        escapeHtml(
            candidate.ticker
        );

    const candidateProfileUrl =
        `ticker-profile.html?ticker=${encodeURIComponent(
            candidate.ticker
        )}`;

    container.innerHTML = `

        <div class="watch-header">

            <div>

                <div class="watch-ticker">

                    <a
                        href="${candidateProfileUrl}"
                        class="ticker-link"
                        aria-label="View ${candidateTicker} ticker profile"
                    >
                        ${candidateTicker}
                    </a>

                </div>

                <div class="watch-setup">
                    ${escapeHtml(
                        candidate.direction
                    )}
                    &bull;
                    ${escapeHtml(
                        candidate.setup
                    )}
                </div>

            </div>

            <div class="watch-score">

                SCORE

                <strong>
                    ${escapeHtml(
                        formatScore(
                            candidate.score
                        )
                    )}
                </strong>

            </div>

        </div>

        <div class="watch-grid">

            <div>
                <span>ENTRY</span>

                <strong>
                    ${escapeHtml(
                        formatPrice(
                            candidate.entry
                        )
                    )}
                </strong>
            </div>

            <div>
                <span>STOP</span>

                <strong>
                    ${escapeHtml(
                        formatPrice(
                            candidate.stop
                        )
                    )}
                </strong>
            </div>

            <div>
                <span>TARGET</span>

                <strong>
                    ${escapeHtml(
                        formatPrice(
                            candidate.target
                        )
                    )}
                </strong>
            </div>

            <div>
                <span>R/R</span>

                <strong>
                    ${escapeHtml(
                        formatRiskReward(rr)
                    )}
                </strong>
            </div>

        </div>

        <div class="watch-actions">

            <a
                href="${candidateProfileUrl}"
                class="ticker-profile-button"
            >
                VIEW ${candidateTicker} TICKER PROFILE →
            </a>

        </div>

        <p>
            This opportunity is being highlighted as a developing
            setup based on its current ranking and available trade
            structure. Traders should independently verify current
            conditions before acting.
        </p>
    `;
}


function findStockToWatch(
    trades
) {
    if (
        trades.length <=
        TOP_PICK_COUNT
    ) {
        return null;
    }

    return trades[
        TOP_PICK_COUNT
    ];
}


function buildTradeDescription(
    trade
) {
    const direction =
        String(
            trade.direction || ""
        ).toLowerCase();

    if (isLong(direction)) {
        return `${trade.ticker} is currently represented as a bullish ` +
               `opportunity within the published NEA28V1 dataset.`;
    }

    if (isShort(direction)) {
        return `${trade.ticker} is currently represented as a bearish ` +
               `opportunity within the published NEA28V1 dataset.`;
    }

    return `${trade.ticker} is currently represented as a qualifying ` +
           `NEA28V1 trade opportunity.`;
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


function firstValue(
    ...values
) {
    for (
        const value of values
    ) {
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


function setPublicationDate() {
    const element =
        document.getElementById(
            "publicationDate"
        );

    if (!element) {
        return;
    }

    const now =
        new Date();

    element.textContent =
        now.toLocaleDateString(
            "en-US",
            {
                year: "numeric",
                month: "long",
                day: "numeric"
            }
        );
}


function renderEmptyState() {
    setText(
        "marketSummary",
        "No qualifying trade data is currently available."
    );

    setText(
        "activeTradeCount",
        "0"
    );

    setText(
        "marketBias",
        "Neutral"
    );

    setText(
        "highestScore",
        "—"
    );

    setText(
        "directionalEnvironment",
        "No Data"
    );

    setText(
        "setupEnvironment",
        "No Data"
    );

    setText(
        "riskEnvironment",
        "No Data"
    );

    const topPicks =
        document.getElementById(
            "topPicks"
        );

    if (topPicks) {
        topPicks.innerHTML =
            `<div class="loading">
                No qualifying trade opportunities are currently available.
             </div>`;
    }

    const watch =
        document.getElementById(
            "stockToWatch"
        );

    if (watch) {
        watch.innerHTML =
            `<div class="loading">
                No developing opportunity is currently available.
             </div>`;
    }
}


function renderDataError() {
    const topPicks =
        document.getElementById(
            "topPicks"
        );

    if (topPicks) {
        topPicks.innerHTML =
            `<div class="loading">
                Unable to load the current NEA28V1 trade dataset.
             </div>`;
    }

    const watch =
        document.getElementById(
            "stockToWatch"
        );

    if (watch) {
        watch.innerHTML =
            `<div class="loading">
                Trade intelligence is temporarily unavailable.
             </div>`;
    }

    setText(
        "marketSummary",
        "The current publication dataset could not be loaded."
    );
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
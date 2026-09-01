async function getJSON(file) {
    const response = await fetch(
        "./data/" + file + "?t=" + Date.now(),
        {
            cache: "no-store"
        }
    );

    if (!response.ok) {
        throw new Error(
            `${file}: HTTP ${response.status}`
        );
    }

    return response.json();
}

function money(value) {
    if (value == null || value === "") {
        return "—";
    }

    const number = Number(value);

    if (!Number.isFinite(number)) {
        return "—";
    }

    return number < 1
        ? "$" + number.toFixed(4)
        : "$" + number.toFixed(2);
}

async function loadTickerTrades(index) {
    const tickerTrades = [];

    const tickers =
        index &&
        typeof index.tickers === "object" &&
        index.tickers !== null
            ? index.tickers
            : {};

    const today =
        getTodayDateKey();

    for (const ticker of Object.keys(tickers)) {
        const dates = Array.isArray(
            tickers[ticker]
        )
            ? tickers[ticker]
            : [];

        if (!dates.length) {
            continue;
        }

        /*
         * TODAY ONLY.
         *
         * A ticker is eligible only when the index contains
         * today's date for that ticker.
         *
         * Never fall back to the latest historical date.
         */
        if (!dates.includes(today)) {
            continue;
        }

        try {
            const data =
                await getJSON(
                    `analysis/${encodeURIComponent(
                        ticker
                    )}/trades.json`
                );

            const trades =
                Array.isArray(data.trades)
                    ? data.trades
                    : [];

            /*
             * Keep ONLY trade records whose actual trade
             * date is today's date.
             */
            const todayTrades =
                trades.filter(
                    trade =>
                        getTradeDate(trade) === today
                );

            if (!todayTrades.length) {
                continue;
            }

            /*
             * If multiple trade records exist for this
             * ticker today, use ONLY the latest one.
             */
            todayTrades.sort(
                (a, b) =>
                    getTradeTimestamp(b) -
                    getTradeTimestamp(a)
            );

            const latestTodayTrade =
                todayTrades[0];

            tickerTrades.push({
                ...latestTodayTrade,
                _ticker: ticker,
                _date: today
            });

        } catch (error) {
            console.error(
                `Failed to load today's trades for ${ticker}:`,
                error
            );
        }
    }

    return tickerTrades;
}


function getTodayDateKey() {
    const now =
        new Date();

    const year =
        now.getFullYear();

    const month =
        String(
            now.getMonth() + 1
        ).padStart(
            2,
            "0"
        );

    const day =
        String(
            now.getDate()
        ).padStart(
            2,
            "0"
        );

    return `${year}-${month}-${day}`;
}


function getTradeDate(trade) {
    if (
        !trade ||
        typeof trade !== "object"
    ) {
        return null;
    }

    /*
     * Use the actual date stored on the trade record.
     *
     * The index date is NOT used as the trade date.
     */
    const dateValue =
        trade.trade_date ??
        trade.tradeDate ??
        trade.date ??
        trade.created_at ??
        trade.createdAt ??
        trade.timestamp ??
        trade.generated_at ??
        trade.generatedAt ??
        trade.updated_at ??
        trade.updatedAt;

    if (
        dateValue === null ||
        dateValue === undefined ||
        dateValue === ""
    ) {
        return null;
    }

    const text =
        String(
            dateValue
        ).trim();

    /*
     * YYYY-MM-DD is already the exact date we need.
     */
    const directMatch =
        text.match(
            /^(\d{4}-\d{2}-\d{2})/
        );

    if (directMatch) {
        return directMatch[1];
    }

    /*
     * Handle full ISO/date timestamps.
     */
    const parsed =
        new Date(
            dateValue
        );

    if (
        Number.isNaN(
            parsed.getTime()
        )
    ) {
        return null;
    }

    return [
        parsed.getFullYear(),
        String(
            parsed.getMonth() + 1
        ).padStart(
            2,
            "0"
        ),
        String(
            parsed.getDate()
        ).padStart(
            2,
            "0"
        )
    ].join("-");
}


function getTradeTimestamp(trade) {
    if (
        !trade ||
        typeof trade !== "object"
    ) {
        return 0;
    }

    const timestamp =
        trade.trade_date ??
        trade.tradeDate ??
        trade.timestamp ??
        trade.created_at ??
        trade.createdAt ??
        trade.generated_at ??
        trade.generatedAt ??
        trade.updated_at ??
        trade.updatedAt;

    if (
        timestamp === null ||
        timestamp === undefined ||
        timestamp === ""
    ) {
        return 0;
    }

    const parsed =
        new Date(
            timestamp
        ).getTime();

    return Number.isFinite(parsed)
        ? parsed
        : 0;
}

function renderTrades(data) {
    const rows =
        document.getElementById("tradeTable");

    if (!rows) {
        return;
    }

    rows.innerHTML = "";

    const trades = Array.isArray(data)
        ? [...data]
        : [];

    trades.sort((a, b) => {
        const aScore = Number(a.score);
        const bScore = Number(b.score);

        const safeA = Number.isFinite(aScore)
            ? aScore
            : -Infinity;

        const safeB = Number.isFinite(bScore)
            ? bScore
            : -Infinity;

        return safeB - safeA;
    });

    trades
        .slice(0, 10)
        .forEach(trade => {

            const row =
                document.createElement("tr");

            row.innerHTML = `
                <td>
                    <b>
                        ${escapeHtml(
                            trade.ticker ||
                            trade._ticker ||
                            ""
                        )}
                    </b>
                </td>

                <td>
                    ${escapeHtml(
                        trade.direction || "—"
                    )}
                </td>

                <td>
                    ${escapeHtml(
                        trade.setup || "—"
                    )}
                </td>

                <td>
                    ${money(trade.entry)}
                </td>

                <td>
                    ${money(trade.stop)}
                </td>

                <td>
                    ${money(trade.target)}
                </td>

                <td>
                    ${
                        Number.isFinite(
                            Number(trade.score)
                        )
                            ? Number(
                                trade.score
                            ).toFixed(2)
                            : "—"
                    }
                </td>

                <td>
                    <span class="badge">
                        ${escapeHtml(
                            trade.status || "—"
                        )}
                    </span>
                </td>
            `;

            rows.appendChild(row);
        });
}

function updateDashboardStats(trades) {
    const tradeList = Array.isArray(trades)
        ? trades
        : [];

    let pending = 0;
    let confirmed = 0;
    let bullish = 0;
    let bearish = 0;

    tradeList.forEach(trade => {

        const status = String(
            trade.status || ""
        ).toUpperCase();

        const direction = String(
            trade.direction || ""
        ).toUpperCase();

        if (status === "PENDING") {
            pending++;
        }

        if (
            status === "CONFIRMED" ||
            status === "OPEN"
        ) {
            confirmed++;
        }

        if (direction === "BULLISH") {
            bullish++;
        }

        if (direction === "BEARISH") {
            bearish++;
        }
    });

    const totalTrades =
        document.getElementById(
            "totalTrades"
        );

    if (totalTrades) {
        totalTrades.textContent =
            tradeList.length;
    }

    const pendingSetups =
        document.getElementById(
            "pendingSetups"
        );

    if (pendingSetups) {
        pendingSetups.textContent =
            pending;
    }

    const confirmedSetups =
        document.getElementById(
            "confirmedSetups"
        );

    if (confirmedSetups) {
        confirmedSetups.textContent =
            confirmed;
    }

    const marketBias =
        document.getElementById(
            "marketBias"
        );

    if (marketBias) {

        let bias = "Neutral";

        if (bullish > bearish) {
            bias = "Impulse";
        } else if (bearish > bullish) {
            bias = "Pullback";
        }

        marketBias.textContent =
            bias;
    }
}

function escapeHtml(value) {
    return String(value)
        .replaceAll(
            "&",
            "&amp;"
        )
        .replaceAll(
            "<",
            "&lt;"
        )
        .replaceAll(
            ">",
            "&gt;"
        )
        .replaceAll(
            '"',
            "&quot;"
        )
        .replaceAll(
            "'",
            "&#039;"
        );
}

async function load() {
    try {
        const index =
            await getJSON(
                "analysis/index.json"
            );

        const trades =
            await loadTickerTrades(
                index
            );

        renderTrades(
            trades
        );

        updateDashboardStats(
            trades
        );

        const lastUpdated =
            document.getElementById(
                "lastUpdated"
            );

        if (lastUpdated) {
            lastUpdated.textContent =
                "Updated " +
                new Date().toISOString();
        }

        const statusDot =
            document.getElementById(
                "statusDot"
            );

        if (statusDot) {
            statusDot.style.background =
                "#55d68a";
        }

    } catch (error) {

        const lastUpdated =
            document.getElementById(
                "lastUpdated"
            );

        if (lastUpdated) {
            lastUpdated.textContent =
                "Data unavailable";
        }

        const statusDot =
            document.getElementById(
                "statusDot"
            );

        if (statusDot) {
            statusDot.style.background =
                "#ff7777";
        }

        console.error(
            "Failed to load public trade data:",
            error
        );
    }
}

load();

setInterval(
    load,
    60000
);
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

    for (const ticker of Object.keys(tickers)) {
        const dates = Array.isArray(
            tickers[ticker]
        )
            ? tickers[ticker]
            : [];

        if (!dates.length) {
            continue;
        }

        const latestDate =
            [...dates].sort().reverse()[0];

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

            trades.forEach(trade => {
                tickerTrades.push({
                    ...trade,
                    _ticker: ticker,
                    _date: latestDate
                });
            });

        } catch (error) {
            console.error(
                `Failed to load trades for ${ticker}:`,
                error
            );
        }
    }

    return tickerTrades;
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
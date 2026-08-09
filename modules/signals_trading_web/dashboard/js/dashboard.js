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

    return Number.isFinite(number)
        ? "$" + number.toFixed(2)
        : "—";
}

function renderTrades(data) {
    const rows =
        document.getElementById("tradeTable");

    if (!rows) {
        return;
    }

    rows.innerHTML = "";

    const trades = Array.isArray(data.trades)
        ? [...data.trades]
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
        .slice(0, 20)
        .forEach(trade => {

            const row =
                document.createElement("tr");

            row.innerHTML = `
                <td>
                    <b>
                        ${escapeHtml(
                            trade.ticker || ""
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

function updateDashboardStats(data) {
    const trades = Array.isArray(data.trades)
        ? data.trades
        : [];

    let pending = 0;
    let confirmed = 0;
    let bullish = 0;
    let bearish = 0;

    trades.forEach(trade => {

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
            trades.length;
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
            bias = "Bullish";
        } else if (bearish > bullish) {
            bias = "Bearish";
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
        const trades =
            await getJSON(
                "trades.json"
            );

        renderTrades(trades);

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
                (
                    trades.generated_at ||
                    ""
                );
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



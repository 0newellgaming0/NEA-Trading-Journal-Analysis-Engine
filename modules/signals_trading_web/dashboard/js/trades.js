let allTrades = [];
let filteredTrades = [];

let currentSort = {
    field: null,
    direction: "asc"
};

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

function normalize(value) {
    return String(value ?? "").toLowerCase();
}

function sortTrades(trades) {
    if (!currentSort.field) {
        return trades;
    }

    const field = currentSort.field;

    return [...trades].sort((a, b) => {
        let valueA = a[field];
        let valueB = b[field];

        const numericFields = [
            "entry",
            "stop",
            "target",
            "risk_reward",
            "current_price",
            "gain_percent"
        ];

        if (numericFields.includes(field)) {
            valueA = Number(valueA ?? 0);
            valueB = Number(valueB ?? 0);
        } else {
            valueA = normalize(valueA);
            valueB = normalize(valueB);
        }

        let result = 0;

        if (valueA < valueB) {
            result = -1;
        } else if (valueA > valueB) {
            result = 1;
        }

        return currentSort.direction === "asc"
            ? result
            : -result;
    });
}

function renderTrades() {
    const rows = document.getElementById("tradeTable");

    if (!rows) {
        return;
    }

    rows.innerHTML = "";

    const sortedTrades = sortTrades(filteredTrades);

    sortedTrades.forEach(trade => {
        const row = document.createElement("tr");

        row.innerHTML = `
            <td>
                <b>${trade.ticker || "—"}</b>
            </td>

            <td>
                ${trade.direction || "—"}
            </td>

            <td>
                ${trade.setup || "—"}
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
                ${trade.risk_reward ?? "—"}
            </td>

            <td>
                <span class="badge">
                    ${trade.status || "—"}
                </span>
            </td>
        `;

        rows.appendChild(row);
    });

    updateSortIndicators();
}

function updateSortIndicators() {
    document
        .querySelectorAll("#tradeTableElement th[data-sort]")
        .forEach(header => {
            const field = header.dataset.sort;

            header.classList.remove(
                "sort-asc",
                "sort-desc"
            );

            if (field === currentSort.field) {
                header.classList.add(
                    currentSort.direction === "asc"
                        ? "sort-asc"
                        : "sort-desc"
                );
            }
        });
}

function searchTrades() {
    const input = document.getElementById(
        "tickerSearch"
    );

    if (!input) {
        filteredTrades = [...allTrades];
        renderTrades();
        return;
    }

    const query = normalize(input.value).trim();

    if (!query) {
        filteredTrades = [...allTrades];
    } else {
        filteredTrades = allTrades.filter(trade =>
            normalize(trade.ticker).includes(query)
        );
    }

    renderTrades();
}

function setupSearch() {
    const input = document.getElementById(
        "tickerSearch"
    );

    const clear = document.getElementById(
        "clearSearch"
    );

    if (input) {
        input.addEventListener(
            "input",
            searchTrades
        );
    }

    if (clear) {
        clear.addEventListener(
            "click",
            () => {
                if (input) {
                    input.value = "";
                }

                filteredTrades = [...allTrades];

                renderTrades();

                if (input) {
                    input.focus();
                }
            }
        );
    }
}

function setupSorting() {
    document
        .querySelectorAll(
            "#tradeTableElement th[data-sort]"
        )
        .forEach(header => {
            header.style.cursor = "pointer";

            header.addEventListener(
                "click",
                () => {
                    const field =
                        header.dataset.sort;

                    if (
                        currentSort.field === field
                    ) {
                        currentSort.direction =
                            currentSort.direction === "asc"
                                ? "desc"
                                : "asc";
                    } else {
                        currentSort.field = field;
                        currentSort.direction = "asc";
                    }

                    renderTrades();
                }
            );
        });
}

function updateStats(data) {
    const trades = Array.isArray(data.trades)
        ? data.trades
        : [];

    const pending = trades.filter(
        trade =>
            normalize(trade.status) === "pending"
    ).length;

    const confirmed = trades.filter(
        trade =>
            normalize(trade.status) === "confirmed"
    ).length;

    const bullish = trades.filter(
        trade =>
            normalize(trade.direction) === "bullish"
    ).length;

    const bearish = trades.filter(
        trade =>
            normalize(trade.direction) === "bearish"
    ).length;

    const pendingElement =
        document.getElementById(
            "pendingSetups"
        );

    if (pendingElement) {
        pendingElement.textContent = pending;
    }

    const confirmedElement =
        document.getElementById(
            "confirmedSetups"
        );

    if (confirmedElement) {
        confirmedElement.textContent = confirmed;
    }

    const biasElement =
        document.getElementById(
            "marketBias"
        );

    if (biasElement) {
        if (bullish > bearish) {
            biasElement.textContent =
                `Bullish (${bullish}/${bearish})`;
        } else if (bearish > bullish) {
            biasElement.textContent =
                `Bearish (${bullish}/${bearish})`;
        } else {
            biasElement.textContent =
                `Neutral (${bullish}/${bearish})`;
        }
    }
}

async function load() {
    try {
        const data =
            await getJSON("trades.json");

        allTrades = Array.isArray(data.trades)
            ? data.trades
            : [];

        filteredTrades = [...allTrades];

        renderTrades();
        updateStats(data);

        const lastUpdated =
            document.getElementById(
                "lastUpdated"
            );

        if (lastUpdated) {
            lastUpdated.textContent =
                "Updated " +
                (data.generated_at || "");
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

setupSearch();
setupSorting();
load();

setInterval(load, 60000);

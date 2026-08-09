let allTrades = [];
let sortColumn = "score";
let sortDirection = "desc";

async function load() {
    try {
        const response = await fetch(
            "./data/trades.json?t=" + Date.now(),
            {
                cache: "no-store"
            }
        );

        if (!response.ok) {
            throw new Error(
                `trades.json HTTP ${response.status}`
            );
        }

        const data = await response.json();

        const updated = document.getElementById("updated");

        if (updated) {
            updated.textContent = data.generated_at || "";
        }

        allTrades = Array.isArray(data.trades)
            ? data.trades
            : [];

        renderTrades();

    } catch (error) {
        const updated = document.getElementById("updated");

        if (updated) {
            updated.textContent = "Data unavailable";
        }

        console.error(
            "Failed to load public trade data:",
            error
        );
    }
}

function renderTrades() {
    const body = document.getElementById("trades");
    const noTrades = document.getElementById("noTrades");
    const tradeCount = document.getElementById("tradeCount");

    if (!body) {
        return;
    }

    const searchInput =
        document.getElementById("tickerSearch");

    const directionFilter =
        document.getElementById("directionFilter");

    const statusFilter =
        document.getElementById("statusFilter");

    const search = searchInput
        ? searchInput.value.trim().toUpperCase()
        : "";

    const direction = directionFilter
        ? directionFilter.value.toUpperCase()
        : "";

    const status = statusFilter
        ? statusFilter.value.toUpperCase()
        : "";

    let trades = allTrades.filter(trade => {
        const ticker = String(
            trade.ticker || ""
        ).toUpperCase();

        const tradeDirection = String(
            trade.direction || ""
        ).toUpperCase();

        const tradeStatus = String(
            trade.status || ""
        ).toUpperCase();

        const matchesSearch =
            !search ||
            ticker.includes(search);

        const matchesDirection =
            !direction ||
            tradeDirection === direction;

        const matchesStatus =
            !status ||
            tradeStatus === status;

        return (
            matchesSearch &&
            matchesDirection &&
            matchesStatus
        );
    });

    trades.sort((a, b) => {
        const aValue = getSortValue(
            a,
            sortColumn
        );

        const bValue = getSortValue(
            b,
            sortColumn
        );

        let comparison = 0;

        if (
            typeof aValue === "number" &&
            typeof bValue === "number"
        ) {
            comparison = aValue - bValue;
        } else {
            comparison = String(aValue).localeCompare(
                String(bValue),
                undefined,
                {
                    numeric: true,
                    sensitivity: "base"
                }
            );
        }

        return sortDirection === "asc"
            ? comparison
            : -comparison;
    });

    body.innerHTML = "";

    trades.forEach(trade => {
        const row = document.createElement("tr");

        const gain =
            trade.gain_percent == null ||
            trade.gain_percent === ""
                ? null
                : Number(trade.gain_percent);

        const score =
            trade.score == null ||
            trade.score === ""
                ? null
                : Number(trade.score);

        const gainClass =
            gain > 0
                ? "positive"
                : gain < 0
                    ? "negative"
                    : "";

        row.innerHTML = `
            <td>
                <b>${escapeHtml(trade.ticker || "")}</b>
            </td>

            <td>
                ${escapeHtml(trade.direction || "—")}
            </td>

            <td>
                ${escapeHtml(trade.setup || "—")}
            </td>

            <td>
                ${money(trade.entry)}
            </td>

            <td>
                ${money(trade.current_price)}
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
                ${
                    score == null ||
                    !Number.isFinite(score)
                        ? "—"
                        : score.toFixed(2)
                }
            </td>

            <td class="${gainClass}">
                ${
                    gain == null ||
                    !Number.isFinite(gain)
                        ? "—"
                        : gain.toFixed(2) + "%"
                }
            </td>

            <td>
                <span class="badge">
                    ${escapeHtml(trade.status || "—")}
                </span>
            </td>
        `;

        body.appendChild(row);
    });

    if (tradeCount) {
        tradeCount.textContent =
            `${trades.length} of ${allTrades.length} trades`;
    }

    if (noTrades) {
        noTrades.hidden =
            trades.length !== 0;
    }

    updateSortHeaders();
}

function getSortValue(trade, column) {
    const numericColumns = [
        "score",
        "entry",
        "current_price",
        "stop",
        "target",
        "risk_reward",
        "gain_percent"
    ];

    if (numericColumns.includes(column)) {
        const value = Number(
            trade[column]
        );

        return Number.isFinite(value)
            ? value
            : -Infinity;
    }

    return String(
        trade[column] ?? ""
    );
}

function updateSortHeaders() {
    document
        .querySelectorAll("th[data-sort]")
        .forEach(th => {
            th.classList.remove(
                "sort-asc",
                "sort-desc"
            );

            if (
                th.dataset.sort ===
                sortColumn
            ) {
                th.classList.add(
                    sortDirection === "asc"
                        ? "sort-asc"
                        : "sort-desc"
                );
            }
        });
}

function money(value) {
    if (
        value == null ||
        value === ""
    ) {
        return "—";
    }

    const number = Number(value);

    return Number.isFinite(number)
        ? "$" + number.toFixed(2)
        : "—";
}

function escapeHtml(value) {
    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}

document
    .querySelectorAll("th[data-sort]")
    .forEach(th => {
        th.addEventListener(
            "click",
            () => {
                const column =
                    th.dataset.sort;

                if (
                    sortColumn ===
                    column
                ) {
                    sortDirection =
                        sortDirection === "asc"
                            ? "desc"
                            : "asc";
                } else {
                    sortColumn = column;
                    sortDirection = "asc";
                }

                renderTrades();
            }
        );
    });

const tickerSearch =
    document.getElementById(
        "tickerSearch"
    );

if (tickerSearch) {
    tickerSearch.addEventListener(
        "input",
        renderTrades
    );
}

const directionFilter =
    document.getElementById(
        "directionFilter"
    );

if (directionFilter) {
    directionFilter.addEventListener(
        "change",
        renderTrades
    );
}

const statusFilter =
    document.getElementById(
        "statusFilter"
    );

if (statusFilter) {
    statusFilter.addEventListener(
        "change",
        renderTrades
    );
}

const clearFilters =
    document.getElementById(
        "clearFilters"
    );

if (clearFilters) {
    clearFilters.addEventListener(
        "click",
        () => {
            if (tickerSearch) {
                tickerSearch.value = "";
            }

            if (directionFilter) {
                directionFilter.value = "";
            }

            if (statusFilter) {
                statusFilter.value = "";
            }

            renderTrades();
        }
    );
}

load();

setInterval(
    load,
    60000
);

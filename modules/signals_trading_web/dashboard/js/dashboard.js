async function getJSON(file) {
    const response = await fetch(
        "../data/" + file + "?t=" + Date.now()
    );

    if (!response.ok) {
        throw new Error(file);
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
    const rows = document.getElementById("tradeTable");

    if (!rows) {
        return;
    }

    rows.innerHTML = "";

    const trades = Array.isArray(data.trades)
        ? data.trades
        : [];

    let open = 0;

    trades.slice(0, 20).forEach(trade => {
        if (
            String(trade.status || "").toUpperCase() === "OPEN"
        ) {
            open++;
        }

        const row = document.createElement("tr");

        row.innerHTML = `
            <td><b>${trade.ticker || ""}</b></td>
            <td>${trade.direction || "—"}</td>
            <td>${trade.setup || "—"}</td>
            <td>${money(trade.entry)}</td>
            <td>${money(trade.stop)}</td>
            <td>${money(trade.target)}</td>
            <td>${trade.risk_reward ?? "—"}</td>
            <td>
                <span class="badge">
                    ${trade.status || "—"}
                </span>
            </td>
        `;

        rows.appendChild(row);
    });

    const openTrades = document.getElementById("openTrades");

    if (openTrades) {
        openTrades.textContent = open;
    }
}


async function load() {
    try {
        const [trades, performance] = await Promise.all([
            getJSON("trades.json"),
            getJSON("performance.json")
        ]);

        renderTrades(trades);

        const winRate = document.getElementById("winRate");

        if (winRate) {
            winRate.textContent =
                (performance.win_rate ?? 0) + "%";
        }

        const netR = document.getElementById("netR");

        if (netR) {
            netR.textContent =
                Number(performance.net_r ?? 0).toFixed(2) + "R";
        }

        const lastUpdated = document.getElementById("lastUpdated");

        if (lastUpdated) {
            lastUpdated.textContent =
                "Updated " + (trades.generated_at || "");
        }

        const statusDot = document.getElementById("statusDot");

        if (statusDot) {
            statusDot.style.background = "#55d68a";
        }

    } catch (error) {
        const lastUpdated = document.getElementById("lastUpdated");

        if (lastUpdated) {
            lastUpdated.textContent = "Data unavailable";
        }

        const statusDot = document.getElementById("statusDot");

        if (statusDot) {
            statusDot.style.background = "#ff7777";
        }

        console.error(
            "Failed to load public trade data:",
            error
        );
    }
}


load();

setInterval(load, 60000);
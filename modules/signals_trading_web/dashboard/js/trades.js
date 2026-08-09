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

        const body = document.getElementById("trades");

        if (!body) {
            return;
        }

        body.innerHTML = "";

        const trades = Array.isArray(data.trades)
            ? data.trades
            : [];

        trades.forEach(trade => {
            const row = document.createElement("tr");

            const gain = (
                trade.gain_percent == null ||
                trade.gain_percent === ""
            )
                ? null
                : Number(trade.gain_percent);

            const gainClass =
                gain > 0
                    ? "positive"
                    : gain < 0
                        ? "negative"
                        : "";

            row.innerHTML = `
                <td><b>${trade.ticker || ""}</b></td>
                <td>${trade.direction || "—"}</td>
                <td>${trade.setup || "—"}</td>
                <td>${money(trade.entry)}</td>
                <td>${money(trade.current_price)}</td>
                <td>${money(trade.stop)}</td>
                <td>${money(trade.target)}</td>
                <td>${trade.risk_reward ?? "—"}</td>
                <td class="${gainClass}">
                    ${
                        gain == null || !Number.isFinite(gain)
                            ? "—"
                            : gain.toFixed(2) + "%"
                    }
                </td>
                <td>
                    <span class="badge">
                        ${trade.status || "—"}
                    </span>
                </td>
            `;

            body.appendChild(row);
        });

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

function money(value) {
    if (value == null || value === "") {
        return "—";
    }

    const number = Number(value);

    return Number.isFinite(number)
        ? "$" + number.toFixed(2)
        : "—";
}

load();

setInterval(load, 60000);
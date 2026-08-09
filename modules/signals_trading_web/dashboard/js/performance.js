async function load() {
    try {
        const response = await fetch(
            "../data/performance.json?t=" + Date.now()
        );

        if (!response.ok) {
            throw new Error("performance.json");
        }

        const data = await response.json();

        const updated = document.getElementById("updated");

        if (updated) {
            updated.textContent = data.generated_at || "";
        }

        const winRate = document.getElementById("winRate");

        if (winRate) {
            winRate.textContent =
                (data.win_rate ?? 0) + "%";
        }

        const totalTrades = document.getElementById("totalTrades");

        if (totalTrades) {
            totalTrades.textContent =
                data.total_trades ?? 0;
        }

        const netR = document.getElementById("netR");

        if (netR) {
            netR.textContent =
                Number(data.net_r ?? 0).toFixed(2) + "R";
        }

        const profitFactor =
            document.getElementById("profitFactor");

        if (profitFactor) {
            profitFactor.textContent =
                Number(data.profit_factor ?? 0).toFixed(2);
        }

        const summary =
            document.getElementById("summary");

        if (summary) {
            summary.innerHTML = `
                <div class="summary-row">
                    <span class="muted">
                        Winning trades
                    </span>
                    <strong>
                        ${data.winning_trades ?? 0}
                    </strong>
                </div>

                <div class="summary-row">
                    <span class="muted">
                        Losing trades
                    </span>
                    <strong>
                        ${data.losing_trades ?? 0}
                    </strong>
                </div>

                <div class="summary-row">
                    <span class="muted">
                        Average R
                    </span>
                    <strong>
                        ${Number(data.average_r ?? 0).toFixed(2)}R
                    </strong>
                </div>

                <div class="summary-row">
                    <span class="muted">
                        Max drawdown
                    </span>
                    <strong>
                        ${Number(
                            data.max_drawdown_percent ?? 0
                        ).toFixed(2)}%
                    </strong>
                </div>
            `;
        }

    } catch (error) {
        const updated = document.getElementById("updated");

        if (updated) {
            updated.textContent = "Data unavailable";
        }

        console.error(
            "Failed to load performance data:",
            error
        );
    }
}


load();

setInterval(load, 60000);
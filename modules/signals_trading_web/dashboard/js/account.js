const API_BASE = "";

let selectedAccountId = null;

function apiKey() {
    return sessionStorage.getItem("NEA_API_KEY") || "";
}

async function apiFetch(url, options = {}) {
    const headers = {
        "Content-Type": "application/json",
        "X-NEA-API-Key": apiKey(),
        ...(options.headers || {})
    };

    const response = await fetch(
        API_BASE + url,
        {
            ...options,
            headers
        }
    );

    let data = {};

    try {
        data = await response.json();
    } catch (error) {
        data = {};
    }

    if (!response.ok) {
        throw new Error(
            data.error ||
            data.message ||
            `HTTP ${response.status}`
        );
    }

    return data;
}

function showError(message) {
    const box = document.getElementById("errorBox");

    if (!box) {
        return;
    }

    box.textContent = message;
    box.style.display = "block";

    setConnectionStatus(false);
}

function clearError() {
    const box = document.getElementById("errorBox");

    if (!box) {
        return;
    }

    box.textContent = "";
    box.style.display = "none";
}

function setConnectionStatus(connected) {
    const status =
        document.getElementById("connectionStatus");

    const text =
        document.getElementById("connectionText");

    if (!status || !text) {
        return;
    }

    status.classList.remove(
        "connected",
        "error"
    );

    if (connected) {
        status.classList.add("connected");
        text.textContent = "Connected";
    } else {
        status.classList.add("error");
        text.textContent = "Connection Error";
    }
}

function formatMoney(value) {
    if (
        value === null ||
        value === undefined ||
        value === ""
    ) {
        return "—";
    }

    const number = Number(value);

    if (!Number.isFinite(number)) {
        return "—";
    }

    return number.toLocaleString(
        "en-US",
        {
            style: "currency",
            currency: "USD"
        }
    );
}

function formatNumber(value) {
    if (
        value === null ||
        value === undefined ||
        value === ""
    ) {
        return "—";
    }

    const number = Number(value);

    if (!Number.isFinite(number)) {
        return "—";
    }

    return number.toLocaleString("en-US");
}

function formatPercent(value) {
    if (
        value === null ||
        value === undefined ||
        value === ""
    ) {
        return "—";
    }

    const number = Number(value);

    if (!Number.isFinite(number)) {
        return "—";
    }

    return number.toFixed(2) + "%";
}

function findValue(object, keys) {
    if (!object) {
        return null;
    }

    for (const key of keys) {
        if (
            object[key] !== undefined &&
            object[key] !== null
        ) {
            return object[key];
        }
    }

    return null;
}

function extractRecords(response, possibleKeys) {
    if (Array.isArray(response)) {
        return response;
    }

    if (!response) {
        return [];
    }

    for (const key of possibleKeys) {
        if (Array.isArray(response[key])) {
            return response[key];
        }
    }

    if (response.data) {
        if (Array.isArray(response.data)) {
            return response.data;
        }

        for (const key of possibleKeys) {
            if (
                Array.isArray(
                    response.data[key]
                )
            ) {
                return response.data[key];
            }
        }
    }

    return [];
}

async function loadAccount() {
    clearError();

    const selector =
        document.getElementById("accountSelector");

    if (selector) {
        selector.innerHTML =
            '<option value="">Loading accounts...</option>';
    }

    try {
        const result =
            await apiFetch("/api/account");

        const accounts =
            extractRecords(
                result,
                [
                    "accounts",
                    "data"
                ]
            );

        if (!selector) {
            return;
        }

        selector.innerHTML = "";

        if (!accounts.length) {
            selector.innerHTML =
                '<option value="">No accounts found</option>';

            selectedAccountId = null;

            setConnectionStatus(true);

            await loadAccountData();

            return;
        }

        accounts.forEach(
            (account, index) => {
                const id =
                    findValue(
                        account,
                        [
                            "account_id",
                            "accountId",
                            "id"
                        ]
                    );

                const label =
                    findValue(
                        account,
                        [
                            "account_name",
                            "accountName",
                            "account_number",
                            "accountNumber",
                            "display_name",
                            "displayName"
                        ]
                    ) ||
                    id ||
                    `Account ${index + 1}`;

                const option =
                    document.createElement("option");

                option.value = id || "";
                option.textContent = label;

                selector.appendChild(option);
            }
        );

        selectedAccountId =
            selector.value || null;

        setConnectionStatus(true);

        await loadAccountData();

    } catch (error) {
        showError(
            "Account: " +
            error.message
        );
    }
}

async function accountChanged() {
    const selector =
        document.getElementById(
            "accountSelector"
        );

    selectedAccountId =
        selector?.value || null;

    clearError();

    await loadAccountData();
}

function accountQuery() {
    if (!selectedAccountId) {
        return "";
    }

    return (
        "?account_id=" +
        encodeURIComponent(
            selectedAccountId
        )
    );
}

async function loadAccountData() {
    await Promise.allSettled([
        loadBalance(),
        loadPositions(),
        loadOpenOrders()
    ]);
}

async function loadBalance() {
    try {
        const result =
            await apiFetch(
                "/api/account/balance" +
                accountQuery()
            );

        const data =
            result.data || result;

        const netValue =
            findValue(
                data,
                [
                    "net_account_value",
                    "netAccountValue",
                    "account_value",
                    "accountValue",
                    "total_assets",
                    "totalAssets",
                    "equity"
                ]
            );

        const cash =
            findValue(
                data,
                [
                    "cash_balance",
                    "cashBalance",
                    "cash",
                    "available_cash",
                    "availableCash"
                ]
            );

        const buyingPower =
            findValue(
                data,
                [
                    "buying_power",
                    "buyingPower",
                    "available_buying_power",
                    "availableBuyingPower"
                ]
            );

        const dayPL =
            findValue(
                data,
                [
                    "day_profit_loss",
                    "dayProfitLoss",
                    "today_profit_loss",
                    "todayProfitLoss",
                    "day_pnl",
                    "dayPnL"
                ]
            );

        document.getElementById(
            "netAccountValue"
        ).textContent =
            formatMoney(netValue);

        document.getElementById(
            "cashBalance"
        ).textContent =
            formatMoney(cash);

        document.getElementById(
            "buyingPower"
        ).textContent =
            formatMoney(buyingPower);

        const plElement =
            document.getElementById(
                "dayProfitLoss"
            );

        plElement.textContent =
            formatMoney(dayPL);

        plElement.classList.remove(
            "positive",
            "negative"
        );

        if (Number(dayPL) > 0) {
            plElement.classList.add("positive");
        } else if (Number(dayPL) < 0) {
            plElement.classList.add("negative");
        }

    } catch (error) {
        showError(
            "Balance: " +
            error.message
        );
    }
}

async function loadPositions() {
    const body =
        document.getElementById(
            "positionsBody"
        );

    if (!body) {
        return;
    }

    try {
        const result =
            await apiFetch(
                "/api/account/positions" +
                accountQuery()
            );

        const positions =
            extractRecords(
                result,
                [
                    "positions",
                    "position",
                    "data"
                ]
            );

        body.innerHTML = "";

        if (!positions.length) {
            body.innerHTML =
                '<tr>' +
                '<td colspan="7" class="muted">' +
                'No open positions.' +
                '</td>' +
                '</tr>';

            return;
        }

        positions.forEach(
            position => {
                const symbol =
                    findValue(
                        position,
                        [
                            "ticker",
                            "symbol",
                            "ticker_symbol"
                        ]
                    ) || "—";

                const quantity =
                    findValue(
                        position,
                        [
                            "quantity",
                            "qty",
                            "position"
                        ]
                    );

                const average =
                    findValue(
                        position,
                        [
                            "average_price",
                            "averagePrice",
                            "avg_price",
                            "avgPrice"
                        ]
                    );

                const market =
                    findValue(
                        position,
                        [
                            "market_price",
                            "marketPrice",
                            "current_price",
                            "currentPrice",
                            "last_price",
                            "lastPrice"
                        ]
                    );

                const marketValue =
                    findValue(
                        position,
                        [
                            "market_value",
                            "marketValue"
                        ]
                    );

                const pnl =
                    findValue(
                        position,
                        [
                            "unrealized_profit_loss",
                            "unrealizedProfitLoss",
                            "unrealized_pnl",
                            "unrealizedPnl"
                        ]
                    );

                const pnlPercent =
                    findValue(
                        position,
                        [
                            "unrealized_profit_loss_percent",
                            "unrealizedProfitLossPercent",
                            "unrealized_pnl_percent",
                            "unrealizedPnlPercent"
                        ]
                    );

                const row =
                    document.createElement("tr");

                row.innerHTML = `
                    <td>${escapeHtml(symbol)}</td>
                    <td>${formatNumber(quantity)}</td>
                    <td>${formatMoney(average)}</td>
                    <td>${formatMoney(market)}</td>
                    <td>${formatMoney(marketValue)}</td>
                    <td class="${
                        Number(pnl) > 0
                            ? "positive"
                            : Number(pnl) < 0
                                ? "negative"
                                : ""
                    }">
                        ${formatMoney(pnl)}
                    </td>
                    <td class="${
                        Number(pnlPercent) > 0
                            ? "positive"
                            : Number(pnlPercent) < 0
                                ? "negative"
                                : ""
                    }">
                        ${formatPercent(pnlPercent)}
                    </td>
                `;

                body.appendChild(row);
            }
        );

    } catch (error) {
        body.innerHTML =
            '<tr>' +
            '<td colspan="7" class="negative">' +
            'Unable to load positions.' +
            '</td>' +
            '</tr>';

        showError(
            "Positions: " +
            error.message
        );
    }
}

async function loadOpenOrders() {
    const body =
        document.getElementById(
            "ordersBody"
        );

    if (!body) {
        return;
    }

    try {
        const result =
            await apiFetch(
                "/api/orders/open" +
                accountQuery()
            );

        const orders =
            extractRecords(
                result,
                [
                    "orders",
                    "data"
                ]
            );

        body.innerHTML = "";

        if (!orders.length) {
            body.innerHTML =
                '<tr>' +
                '<td colspan="6" class="muted">' +
                'No open orders.' +
                '</td>' +
                '</tr>';

            return;
        }

        orders.forEach(
            order => {
                const symbol =
                    findValue(
                        order,
                        [
                            "ticker",
                            "symbol",
                            "ticker_symbol"
                        ]
                    ) || "—";

                const side =
                    findValue(
                        order,
                        [
                            "side",
                            "action"
                        ]
                    ) || "—";

                const type =
                    findValue(
                        order,
                        [
                            "order_type",
                            "orderType",
                            "type"
                        ]
                    ) || "—";

                const quantity =
                    findValue(
                        order,
                        [
                            "quantity",
                            "qty"
                        ]
                    );

                const price =
                    findValue(
                        order,
                        [
                            "limit_price",
                            "limitPrice",
                            "price",
                            "lmt_price"
                        ]
                    );

                const status =
                    findValue(
                        order,
                        [
                            "status",
                            "order_status",
                            "orderStatus"
                        ]
                    ) || "—";

                const row =
                    document.createElement("tr");

                row.innerHTML = `
                    <td>${escapeHtml(symbol)}</td>
                    <td>${escapeHtml(side)}</td>
                    <td>${escapeHtml(type)}</td>
                    <td>${formatNumber(quantity)}</td>
                    <td>${formatMoney(price)}</td>
                    <td>${escapeHtml(status)}</td>
                `;

                body.appendChild(row);
            }
        );

    } catch (error) {
        body.innerHTML =
            '<tr>' +
            '<td colspan="6" class="negative">' +
            'Unable to load orders.' +
            '</td>' +
            '</tr>';

        showError(
            "Orders: " +
            error.message
        );
    }
}

function escapeHtml(value) {
    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}

loadAccount();
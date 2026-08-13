import os
import uuid

from webull.core.client import ApiClient
from webull.trade.trade_client import TradeClient


class WebullClient:

    def __init__(self):
        self.app_key = os.environ["WEBULL_APP_KEY"]
        self.app_secret = os.environ["WEBULL_APP_SECRET"]
        self.access_token = os.environ.get("WEBULL_ACCESS_TOKEN")
        self.account_id = os.environ.get("WEBULL_ACCOUNT_ID")

        self.region = os.environ.get(
            "WEBULL_REGION",
            "us"
        )

        self.endpoint = os.environ.get(
            "WEBULL_API_ENDPOINT",
            "api.webull.com"
        )

        self.api_client = ApiClient(
            self.app_key,
            self.app_secret,
            self.region
        )

        self.api_client.add_endpoint(
            self.region,
            self.endpoint
        )

        self.trade_client = TradeClient(
            self.api_client
        )

    def _response(self, response):
        if response is None:
            raise RuntimeError(
                "Webull returned no response."
            )

        status_code = getattr(
            response,
            "status_code",
            None
        )

        if status_code != 200:
            text = getattr(
                response,
                "text",
                ""
            )

            raise RuntimeError(
                f"Webull API error "
                f"{status_code}: {text}"
            )

        return response.json()

    def get_accounts(self):
        response = (
            self.trade_client
            .account_v2
            .get_account_list()
        )

        return self._response(response)

    def resolve_account_id(self):
        if self.account_id:
            return self.account_id

        accounts = self.get_accounts()

        if not accounts:
            raise RuntimeError(
                "Webull returned no accounts."
            )

        if isinstance(accounts, dict):
            accounts = accounts.get(
                "accounts",
                accounts.get(
                    "data",
                    []
                )
            )

        if not accounts:
            raise RuntimeError(
                "No Webull account records found."
            )

        account = accounts[0]

        self.account_id = (
            account.get("account_id")
            or account.get("accountId")
        )

        if not self.account_id:
            raise RuntimeError(
                "Webull account_id missing."
            )

        return self.account_id

    def get_balance(self):
        account_id = self.resolve_account_id()

        response = (
            self.trade_client
            .account_v2
            .get_account_balance(
                account_id
            )
        )

        return self._response(response)

    def get_positions(self):
        account_id = self.resolve_account_id()

        response = (
            self.trade_client
            .account_v2
            .get_account_position(
                account_id
            )
        )

        return self._response(response)

    def get_open_orders(self):
        account_id = self.resolve_account_id()

        response = (
            self.trade_client
            .order_v3
            .get_order_open(
                account_id
            )
        )

        return self._response(response)

    def get_order_history(
        self,
        page_size=None,
        start_date=None,
        end_date=None
    ):
        account_id = self.resolve_account_id()

        kwargs = {}

        if page_size is not None:
            kwargs["page_size"] = page_size

        if start_date is not None:
            kwargs["start_date"] = start_date

        if end_date is not None:
            kwargs["end_date"] = end_date

        response = (
            self.trade_client
            .order_v3
            .get_order_history(
                account_id,
                **kwargs
            )
        )

        return self._response(response)

    def preview_order(self, new_order):
        account_id = self.resolve_account_id()

        client_order_id = uuid.uuid4().hex

        order = self._build_order(
            new_order,
            client_order_id
        )

        response = (
            self.trade_client
            .order_v3
            .preview_order(
                account_id,
                [order]
            )
        )

        result = self._response(response)

        return {
            "client_order_id": client_order_id,
            "order": order,
            "preview": result
        }

    def place_order(self, new_order):
        account_id = self.resolve_account_id()

        client_order_id = uuid.uuid4().hex

        order = self._build_order(
            new_order,
            client_order_id
        )

        response = (
            self.trade_client
            .order_v3
            .place_order(
                account_id,
                [order]
            )
        )

        result = self._response(response)

        if isinstance(result, dict):
            result["client_order_id"] = (
                client_order_id
            )

        return result

    def preview_orders(self, orders):
        account_id = self.resolve_account_id()

        built_orders = []

        for source in orders:
            client_order_id = uuid.uuid4().hex

            built_orders.append(
                self._build_order(
                    source,
                    client_order_id
                )
            )

        response = (
            self.trade_client
            .order_v3
            .preview_order(
                account_id,
                built_orders
            )
        )

        return {
            "orders": built_orders,
            "preview": self._response(response)
        }

    def place_orders(self, orders):
        account_id = self.resolve_account_id()

        built_orders = []

        for source in orders:
            client_order_id = uuid.uuid4().hex

            built_orders.append(
                self._build_order(
                    source,
                    client_order_id
                )
            )

        response = (
            self.trade_client
            .order_v3
            .place_order(
                account_id,
                built_orders
            )
        )

        result = self._response(response)

        return {
            "orders": built_orders,
            "result": result
        }

    def batch_place_order(self, orders):
        """
        Submit a Webull V3 batch/combo payload.

        This method is intentionally separate from
        place_orders(). It does not convert a protective
        OTOCO structure into independent orders.
        """

        account_id = self.resolve_account_id()

        response = (
            self.trade_client
            .order_v3
            .batch_place_order(
                account_id,
                orders
            )
        )

        return self._response(response)

    def _build_order(
        self,
        source,
        client_order_id
    ):
        ticker = (
            str(
                source["ticker"]
            )
            .strip()
            .upper()
        )

        side = (
            str(
                source["side"]
            )
            .strip()
            .upper()
        )

        order_type = (
            str(
                source.get(
                    "order_type",
                    "LIMIT"
                )
            )
            .strip()
            .upper()
        )

        tif = (
            str(
                source.get(
                    "time_in_force",
                    "DAY"
                )
            )
            .strip()
            .upper()
        )

        quantity = int(
            source["quantity"]
        )

        entry = float(
            source["entry"]
        )

        if (
            not ticker
            or quantity <= 0
            or entry <= 0
        ):
            raise ValueError(
                "Invalid order parameters."
            )

        if side not in {
            "BUY",
            "SELL"
        }:
            raise ValueError(
                "Invalid order side."
            )

        if order_type not in {
            "LIMIT",
            "MARKET"
        }:
            raise ValueError(
                "Only LIMIT and MARKET "
                "orders are currently enabled."
            )

        order = {
            "combo_type":
                "NORMAL",

            "client_order_id":
                client_order_id,

            "symbol":
                ticker,

            "instrument_type":
                "EQUITY",

            "market":
                "US",

            "order_type":
                order_type,

            "quantity":
                str(quantity),

            "side":
                side,

            "time_in_force":
                tif,

            "support_trading_session":
                source.get(
                    "support_trading_session",
                    "CORE"
                ),

            "entrust_type":
                "QTY"
        }

        if order_type == "LIMIT":
            order["limit_price"] = (
                f"{entry:.4f}"
            )

        return order
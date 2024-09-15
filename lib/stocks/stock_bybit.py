import logging

import json5

from pybit.unified_trading import WebSocket
from pybit.unified_trading import HTTP

from lib.stocks.stock_interface import IStock
from lib import utils


class StockBybit(IStock):

    def __init__(self, account_name=None, api_secrets_file=None, settings_file=None):
        self.log = logging.getLogger(__name__)
        self.log.info(f"Connecting to public Bybit ...")
        self.http = HTTP(demo=True)
        self.http_private = None
        self.ws = None
        if account_name:
            self.log.info(f"Connecting to private Bybit: {account_name} ...")

            with open(api_secrets_file) as f:
                api_secrets = json5.load(f)
            with open(settings_file) as f:
                settings = json5.load(f)

            self.log.info("Current settings:")
            self.log.info(json5.dumps(settings, indent=4))

            # You can create an authenticated or unauthenticated HTTP session.
            # You can skip authentication by not passing any value for the key and secret.
            self.http_private = HTTP(
                api_key=api_secrets["accounts"][account_name]["API_KEY"],
                api_secret=api_secrets["accounts"][account_name]["API_SECRET"],
                demo=True,
            )

        super().__init__()

    def _value_to_qty(self, value, symbol):
        """
        https://bybit-exchange.github.io/docs/v5/market/tickers
        """
        tickers = self.http_private.get_tickers(category="linear", symbol=symbol)
        mp = tickers["result"]["list"][0]["markPrice"]
        qty = value / float(mp)
        self.log.info(f"value_to_qty {symbol} price {mp}: {value} -> {qty}")
        if symbol == "BTCUSDT":
            qty = round(qty, 3)
        return qty

    def _create_market(self, order_id, side, symbol, value, stopLoss, takeProfit):
        """

        https://bybit-exchange.github.io/docs/v5/order/create-order

        symbol: BTCUSDT
        :param side: SHORT, LONG
        :return:
        """
        if side == "LONG":
            side = "Buy"
            positionIdx = 1
        elif side == "SHORT":
            side = "Sell"
            positionIdx = 2
        positionIdx = 0
        # Place an order on that USDT Perpetual
        self.log.info(
            self.http_private.place_order(
                category="linear",
                orderLinkId=order_id,
                symbol=symbol,
                isLeverage=1,
                side=side,
                orderType="Market",
                qty=self._value_to_qty(value, symbol),
                # Used to identify positions in different position modes. Under hedge-mode, this param is required
                # 0: one-way mode
                # 1: hedge-mode Buy side
                # 2: hedge-mode Sell side
                positionIdx=positionIdx,
                takeProfit=takeProfit,
                stopLoss=stopLoss,
                # https://www.bybit.com/en/help-center/article/What-Are-Time-In-Force-TIF-GTC-IOC-FOK
                timeInForce="IOC",
                tpTriggerBy="LastPrice",
                slTriggerBy="LastPrice",
                tpslMode="Full",
            )
        )

    def _create_limit(self, order_id, side, symbol, price, stopLoss, takeProfit):
        """

        https://bybit-exchange.github.io/docs/v5/order/create-order

        symbol: BTCUSDT
        :param side: SHORT, LONG
        :return:
        """
        if side == "LONG":
            side = "Buy"
            positionIdx = 1
        elif side == "SHORT":
            side = "Sell"
            positionIdx = 2
        # Place an order on that USDT Perpetual
        self.log.info(
            self.http_private.place_order(
                category="linear",
                orderLinkId=order_id,
                symbol=symbol,
                isLeverage=1,
                side=side,
                orderType="Limit",
                price=price,
                # Used to identify positions in different position modes. Under hedge-mode, this param is required
                # 0: one-way mode
                # 1: hedge-mode Buy side
                # 2: hedge-mode Sell side
                positionIdx=positionIdx,
                takeProfit=takeProfit,
                stopLoss=stopLoss,
                # https://www.bybit.com/en/help-center/article/What-Are-Time-In-Force-TIF-GTC-IOC-FOK
                timeInForce="IOC",
                tpTriggerBy="LastPrice",
                slTriggerBy="LastPrice",
                tpslMode="Full",
            )
        )

    def _get_current_USDT_deposit(self):
        wb = self.http_private.get_wallet_balance(accountType="UNIFIED")
        for coin in wb["result"]["list"][0]["coin"]:
            if coin["coin"] == "USDT":
                return coin["walletBalance"]

    def open_SHORT(self, uid, price, amount, stopLimit, takeProfit, limit=None):
        pass

    def open_LONG(self, uid, price, amount, stopLimit, takeProfit, limit=None):
        pass

    def close_SHORT_LONG(self, uid, limit=None):
        pass

    def get_history_tohlcv(self, pair, interval, start, end=None):
        kargs = {
            "category": "linear",
            "symbol": pair,
            "interval": interval,
            "start": utils.datetime_text_to_ts(start),
        }
        if end:
            kargs["end"] = utils.datetime_text_to_ts(end)

        # TODO: it doesnt return everything! probably pagination
        return self.http.get_kline(**kargs)["result"]["list"]

    def stream_ticker(self, pair, handler, stop_event):
        self.log.info(f"Connecting to public Bybit ws stream ...")
        self.ws = WebSocket(
            testnet=True,  # testnet gives wrong values! at least on HTTP
            channel_type="linear"
        )

        def handle_ticker(message):
            # reformat here
            handler(message)

        self.ws.ticker_stream(pair, handle_ticker)

        while not stop_event.is_set():
            pass

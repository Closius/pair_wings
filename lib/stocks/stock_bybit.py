import logging
import queue

import json5

from pybit.unified_trading import WebSocket
from pybit.unified_trading import HTTP

from lib.stocks.stock_interface import IStock
from lib import utils

from lib.stocks.db_map.map_interface import IMap


class StockBybit(IStock):

    def __init__(self, map: IMap, account_name=None, api_secrets_file=None, settings_file=None):
        self.log = logging.getLogger(__name__)
        self.log.info(f"Connecting to public Bybit ...")
        self.http = HTTP(demo=True)
        self.http_private = None
        self.ws = None
        self.map = map
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

        super().__init__(map=map)

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
        # It is not efficient but allow to use an universal DataCollector
        for candle in self.http.get_kline(**kargs)["result"]["list"]:
            yield {x[0]: x[1] for x in zip(self.map.candle.get_db_names(), candle)}

    def stream_ticker(self, pair, stop_event):
        self.log.info(f"Connecting to public Bybit ws stream ...")
        self.ws = WebSocket(
            testnet=True,  # testnet gives wrong values! at least on HTTP
            channel_type="linear"
        )
        q = queue.Queue()

        def handle_ticker(message):
            # reformat
            try:
                message["data"].update({"ts": message["ts"]})
                d = {x[1]: message["data"][x[0]]
                     for x in list(zip(self.map.ticker.get_api_names(), self.map.ticker.get_db_names()))}
                q.put(d)
            except Exception as ex:
                self.log.exception(ex)

        self.ws.ticker_stream(pair, handle_ticker)

        while not stop_event.is_set():
            yield q.get(block=True)

    def stream_order_book(self, pair, stop_event):
        """

        https://bybit-exchange.github.io/docs/v5/websocket/public/orderbook

Process snapshot/delta
To process snapshot and delta messages, please follow these rules:

Once you have subscribed successfully, you will receive a snapshot.
The WebSocket will keep pushing delta messages every time the orderbook
changes. If you receive a new snapshot message, you will have to reset
 your local orderbook. If there is a problem on Bybit's end, a
 snapshot will be re-sent, which is guaranteed to contain the latest data.

To apply delta updates:

If you receive an amount that is 0, delete the entry
If you receive an amount that does not exist, insert it
If the entry exists, you simply update the value
See working code examples of this logic in the FAQ.

        :param pair:
        :param stop_event:
        :return:

        {
    "topic": "orderbook.50.BTCUSDT",
    "type": "snapshot",
    "ts": 1672304484978,
    "data": {
        "s": "BTCUSDT",


            > b	array	Bids. For snapshot stream, the element is sorted by price in descending order
            >> b[0]	string	Bid price
            >> b[1]	string	Bid size
            The delta data has size=0, which means that all quotations for this price have been filled or cancelled

        "b": [
            ...,
            [
                "16493.50",
                "0.006"
            ],
            [
                "16493.00",
                "0.100"
            ]
        ],


            > a	array	Asks. For snapshot stream, the element is sorted by price in ascending order
            >> a[0]	string	Ask price
            >> a[1]	string	Ask size
            The delta data has size=0, which means that all quotations for this price have been filled or cancelled



        "a": [
            [
                "16611.00",
                "0.029"
            ],
            [
                "16612.00",
                "0.213"
            ],
            ...,
        ],


        > u	integer	Update ID. Is a sequence. Occasionally, you'll receive
        "u"=1, which is a snapshot data due to the restart of the
        service. So please overwrite your local orderbook


    "u": 18521288,

        > seq	integer	Cross sequence
        You can use this field to compare different levels orderbook data,
        and for the smaller seq, then it means the data is generated earlier.


    "seq": 7961638724
    }

        cts	number	The timestamp from the match engine when this
        orderbook data is produced. It can be correlated with T
        from public trade channel


    "cts": 1672304484976
}


        """






        self.log.info(f"Connecting to public Bybit ws stream ...")
        self.ws = WebSocket(
            testnet=True,  # testnet gives wrong values! at least on HTTP
            channel_type="linear"
        )
        q = queue.Queue()

        def handle_ticker(message):
            # reformat
            try:
                message["data"].update({"ts": message["ts"]})
                d = {x[1]: message["data"][x[0]]
                     for x in list(zip(self.map.ticker.get_api_names(), self.map.ticker.get_db_names()))}
                q.put(d)
            except Exception as ex:
                self.log.exception(ex)

        self.ws.orderbook_stream(depth=50, symbol=pair, callback=handle_ticker)


        while not stop_event.is_set():
            yield q.get(block=True)
import json5
import numpy as np

from pybit.unified_trading import WebSocket
from pybit.unified_trading import HTTP

from lib.stocks.stock_interface import IStock
from lib import utils

from lib.stocks.db_map.map_interface import IMap


class StockBybit(IStock):

    def __init__(self, map: IMap, account_name=None, api_secrets_file=None, settings_file=None):
        super().__init__(map=map)
        self.log.info(f"Connecting to public Bybit ...")
        self.http = HTTP(demo=True)
        self.http_private = None
        self.ws = WebSocket(
            testnet=True,  # testnet gives wrong values! at least on HTTP
            channel_type="linear"
        )
        self.ws_private = None
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
            nss = {}
            for db_name, data in zip(self.map.candle.get_db_names(), candle):
                if db_name == self.map.candle.Time.db_name:
                    nss[db_name] = utils.ts_to_datetime(data)
                else:
                    nss[db_name] = data

            yield nss

    @IStock.stream_decorator
    def stream_tohlcv(self, handler, handler_kwargs, stop_event, pair, interval):
        """
        https://bybit-exchange.github.io/docs/v5/websocket/public/kline
        """

        def handle_kline(message):
            # reformat
            try:
                data = message["data"][0]
                d = {}
                for api_name, db_name in zip(self.map.candle_ticker.get_api_names(), self.map.candle_ticker.get_db_names()):
                    if db_name in [self.map.candle_ticker.Time.db_name,
                                   self.map.candle_ticker.Start.db_name,
                                   self.map.candle_ticker.End.db_name]:
                        d[db_name] = utils.ts_to_datetime(data[api_name])
                    else:
                        d[db_name] = data[api_name]

                handler(d, **handler_kwargs)
            except Exception as ex:
                self.log.exception(ex)

        self.ws.kline_stream(interval, pair, handle_kline)

        while not stop_event.is_set():
            pass

    @IStock.stream_decorator
    def stream_ticker(self, handler, handler_kwargs, stop_event, pair):

        def handle_ticker(message):
            # reformat
            try:
                message["data"].update({"ts": message["ts"]})
                d = {}
                for api_name, db_name in zip(self.map.ticker.get_api_names(), self.map.ticker.get_db_names()):
                    if db_name == self.map.ticker.Time.db_name:
                        d[db_name] = utils.ts_to_datetime(message["data"][api_name])
                    else:
                        d[db_name] = message["data"][api_name]

                handler(d, **handler_kwargs)
            except Exception as ex:
                self.log.exception(ex)

        self.ws.ticker_stream(pair, handle_ticker)

        while not stop_event.is_set():
            pass

    @IStock.stream_decorator
    def stream_order_book(self, handler, handler_kwargs, stop_event, pair):
        """
            https://bybit-exchange.github.io/docs/v5/websocket/public/orderbook
        """

        def handle_ticker(message):
            handle_ticker.asks_d_snapshot = None
            handle_ticker.bids_d_snapshot = None

            def asks_bids_delta_snapshot(raw_data, is_snapshot, big_snapshot: dict | None) -> dict | None:
                df = {float(p): float(v) for p, v in raw_data}
                if is_snapshot:
                    return df
                else:
                    if isinstance(big_snapshot, dict):
                        res = {}
                        for p, v in big_snapshot.items():
                            if p not in df:
                                continue
                            elif df[p] == 0:
                                continue
                            else:
                                res[p] = df[p]
                        return res
                    else:
                        return None

            # reformat
            try:
                is_snapshot = True if message["type"] == "snapshot" else False

                d = {}
                d[self.map.order_book.Time.db_name] = utils.ts_to_datetime(message["ts"])

                handle_ticker.asks_d_snapshot = asks_bids_delta_snapshot(raw_data=message["data"][self.map.order_book.Asks.api_name],
                                                    is_snapshot=is_snapshot,
                                                    big_snapshot=handle_ticker.asks_d_snapshot)
                if handle_ticker.asks_d_snapshot is None:
                    return
                else:
                    d[self.map.order_book.Asks.db_name] = np.array([[p,v] for p,v in handle_ticker.asks_d_snapshot.items()])

                handle_ticker.bids_d_snapshot = asks_bids_delta_snapshot(raw_data=message["data"][self.map.order_book.Bids.api_name],
                                                    is_snapshot=is_snapshot,
                                                    big_snapshot=handle_ticker.bids_d_snapshot)
                if handle_ticker.bids_d_snapshot is None:
                    return
                else:
                    d[self.map.order_book.Bids.db_name] = np.array([[p,v] for p,v in handle_ticker.bids_d_snapshot.items()])

                handler(d, **handler_kwargs)
            except Exception as ex:
                self.log.exception(ex)

        self.ws.orderbook_stream(depth=50, symbol=pair, callback=handle_ticker)

        while not stop_event.is_set():
            pass

import json
import time

import json5
import numpy as np

from pybit.unified_trading import WebSocket
from pybit.unified_trading import HTTP

from lib.stocks.stock_interface import IStock
from lib import utils

from lib.stocks.db_map.map_interface import IMap, ITicker, ICandle, ICandleTicker, IOrderBook, IPosition


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
        if account_name:
            self.log.info(f"Connecting to private Bybit: {account_name} ...")

            with open(api_secrets_file) as f:
                api_secrets = json5.load(f)
            with open(settings_file) as f:
                settings = json5.load(f)

            # self.log.info("Current settings:")
            # self.log.info(json5.dumps(settings, indent=4))

            # You can create an authenticated or unauthenticated HTTP session.
            # You can skip authentication by not passing any value for the key and secret.
            self.http_private = HTTP(
                api_key=api_secrets["accounts"][account_name]["API_KEY"],
                api_secret=api_secrets["accounts"][account_name]["API_SECRET"],
                demo=True,
            )

            self.ws_private = WebSocket(
                demo=True,
                testnet=False,
                channel_type="private",
                api_key=api_secrets["accounts"][account_name]["API_KEY"],
                api_secret=api_secrets["accounts"][account_name]["API_SECRET"],
            )

    def _amount_money_to_qty(self, amount_money, symbol):
        """
        https://bybit-exchange.github.io/docs/v5/market/tickers
        """
        tickers = self.http_private.get_tickers(category="linear", symbol=symbol)
        mp = tickers["result"]["list"][0]["markPrice"]
        qty = amount_money / float(mp)
        self.log.info(f"value_to_qty {symbol} price {mp}: {amount_money} -> {qty}")
        if symbol == "BTCUSDT":
            qty = round(qty, 3)
        return qty

    def _get_current_USDT_deposit(self):
        wb = self.http_private.get_wallet_balance(accountType="UNIFIED")
        for coin in wb["result"]["list"][0]["coin"]:
            if coin["coin"] == "USDT":
                return coin["walletBalance"]

    def open_modify_SHORT_LONG(self, side, pair, amount_money_add=None, stopLoss=None, takeProfit=None):
        if amount_money_add and amount_money_add <= 0:
            raise ValueError("amount_money must be > 0. HINT: To close the position use "
                             "close_SHORT_LONG() or open the opposite position")
        pos_info = self.get_position_status(pair=pair)
        # self.log.info(json5.dumps(pos_info, indent=4))
        if pos_info is None:
            msg = f"Opening {side} position: {amount_money_add} money on {pair}, stopLoss={stopLoss}, takeProfit={takeProfit}"
        else:
            w_msg = []
            if amount_money_add:
                w_msg.append(f"add {amount_money_add} money")
            if stopLoss:
                if stopLoss != pos_info.StopLoss:
                    w_msg.append(f"stopLoss={stopLoss}")
            if takeProfit:
                if takeProfit != pos_info.TakeProfit:
                    w_msg.append(f"takeProfit={takeProfit}")
            if len(w_msg) == 0:
                raise ValueError("Nothing to do")
            msg = f"Modifying to {side} position ({pos_info.Size * pos_info.MarkPrice_} money) on {pair}: " + ", ".join(w_msg)

        self.log.info(msg)

        if side == "LONG":
            side = "Buy"
        elif side == "SHORT":
            side = "Sell"

        kwrgs = {
            "category": "linear",
            "symbol": pair,
            "isLeverage": 1,
            "side": side,
            "orderType": "Market",
            "qty": self._amount_money_to_qty(amount_money_add, pair),
            # Used to identify positions in different position modes. Under hedge-mode, this param is required
            # 0: one-way mode
            # 1: hedge-mode Buy side
            # 2: hedge-mode Sell side
            "positionIdx": 0,
            # https://www.bybit.com/en/help-center/article/What-Are-Time-In-Force-TIF-GTC-IOC-FOK
            "timeInForce": "IOC",
            "tpTriggerBy": "LastPrice",
            "slTriggerBy": "LastPrice",
            "tpslMode": "Full"
        }
        if stopLoss:
            kwrgs["stopLoss"] = stopLoss
        if takeProfit:
            kwrgs["takeProfit"] = takeProfit

        # Place an order on that USDT Perpetual
        orderId = self.http_private.place_order(**kwrgs)['result']['orderId']

        self.log.info(f"<< Completed >>. {msg}")

        return orderId

    def close_SHORT_LONG(self, pair, amount_percent=100):
        """
        Close by market price

        if amount_percent=100 - all the qty (coins) will be closed

        :param uid:
        :return:
        """
        msg = f"Closing position: {amount_percent} % on {pair}"
        self.log.info(msg)
        if (amount_percent > 100) or (amount_percent <= 0):
            raise ValueError(f"amount_percent should be 100>x>=0")
        pos_info = self.get_position_status(pair=pair)
        if pos_info is None:
            raise ValueError("current position is zero, nothing to close")
        original_position_size = pos_info.Size
        size_coins_to_close = original_position_size * (amount_percent / 100)
        side = pos_info.Side
        size_to_close = "Sell" if side == "LONG" else "Buy"

        # https://stackoverflow.com/questions/71056977/how-can-i-closing-my-position-with-using-market-order-via-bybit-api
        orderId = self.http_private.place_order(
                category="linear",
                symbol=pair,
                side=size_to_close,
                orderType="Market",
                qty=size_coins_to_close,
                # https://www.bybit.com/en/help-center/article/What-Are-Time-In-Force-TIF-GTC-IOC-FOK
                timeInForce="GTC",
                reduceOnly=True,
                closeOnTrigger=False
            )['result']['orderId']

        current_order_size = None
        while (original_position_size - size_coins_to_close) != current_order_size:
            pos_info = self.get_position_status(pair=pair)
            if pos_info is None:
                break
            time.sleep(0.5)
            current_order_size = pos_info.Size

        self.log.info(f"<< Completed >>. {msg}")

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
            response = ICandle()
            for (k,v), data in zip(self.map.candle.init_fields.items(), candle):
                if v.db_name == self.map.candle.Time.db_name:
                    setattr(response, k, utils.ts_to_datetime(data))
                else:
                    setattr(response, k, data)

            yield response

    def get_ticker(self, pair):
        message = self.http_private.get_tickers(category="linear",
            symbol=pair)

        response = ITicker()
        response.Time = utils.ts_to_datetime(message["time"])
        message = message["result"]["list"][0]
        for k, v in self.map.ticker.init_fields.items():
            if v.db_name == self.map.ticker.Time.db_name:
                continue
            else:
                setattr(response, k, float(message[v.api_name]))
        return response

    def get_position_status(self, pair, verbose=False):
        pos_info = self.http_private.get_positions(
            category="linear",
            symbol=pair,
        )
        if (len(pos_info["result"]["list"]) == 0) or (pos_info["result"]["list"][0]["size"] == "0"):
            return None
        data = pos_info["result"]["list"][0]
        if verbose:
            self.log.info(f"Position on {pair}:")
            self.log.info(json.dumps(data, indent=4))
        response = IPosition()
        response.CreatedTime = utils.ts_to_datetime(data[self.map.position.CreatedTime.api_name])
        response.UpdatedTime = utils.ts_to_datetime(data[self.map.position.UpdatedTime.api_name])
        response.Side = "SHORT" if data[self.map.position.Side.api_name] == "Sell" else "LONG"
        response.Size = float(data[self.map.position.Size.api_name])
        response.MarkPrice_ = float(data[self.map.position.MarkPrice_.api_name])
        response.StopLoss = None if data[self.map.position.StopLoss.api_name] == "" else float(data[self.map.position.StopLoss.api_name])
        response.TakeProfit = None if data[self.map.position.TakeProfit.api_name] == "" else float(data[self.map.position.TakeProfit.api_name])

        response.Profit_ = float(data["unrealisedPnl"]) + float(data["curRealisedPnl"])

        return response

    @IStock.stream_decorator
    def stream_tohlcv(self, handler, handler_kwargs, stop_event, pair, interval):
        """
        https://bybit-exchange.github.io/docs/v5/websocket/public/kline
        """

        def handle_kline(message):
            # reformat
            try:
                data = message["data"][0]
                response = ICandleTicker()
                for k, v in self.map.candle_ticker.init_fields.items():
                    if v.db_name in [self.map.candle_ticker.Time.db_name,
                                   self.map.candle_ticker.Start.db_name,
                                   self.map.candle_ticker.End.db_name]:
                        setattr(response, k, utils.ts_to_datetime(data[v.api_name]))
                    else:
                        setattr(response, k, data[v.api_name])

                handler(response, **handler_kwargs)
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
                response = ITicker()
                for k, v in self.map.ticker.init_fields.items():
                    if v.db_name == self.map.ticker.Time.db_name:
                        setattr(response, k, utils.ts_to_datetime(message["data"][v.api_name]))
                    else:
                        setattr(response, k, message["data"][v.api_name])

                handler(response, **handler_kwargs)
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

                response = IOrderBook()

                response.Time = utils.ts_to_datetime(message["ts"])

                handle_ticker.asks_d_snapshot = asks_bids_delta_snapshot(raw_data=message["data"][self.map.order_book.Asks.api_name],
                                                    is_snapshot=is_snapshot,
                                                    big_snapshot=handle_ticker.asks_d_snapshot)
                if handle_ticker.asks_d_snapshot is None:
                    return
                else:
                    response.Asks = np.array([[p,v] for p,v in handle_ticker.asks_d_snapshot.items()])

                handle_ticker.bids_d_snapshot = asks_bids_delta_snapshot(raw_data=message["data"][self.map.order_book.Bids.api_name],
                                                    is_snapshot=is_snapshot,
                                                    big_snapshot=handle_ticker.bids_d_snapshot)
                if handle_ticker.bids_d_snapshot is None:
                    return
                else:
                    response.Bids = np.array([[p,v] for p,v in handle_ticker.bids_d_snapshot.items()])

                handler(response, **handler_kwargs)
            except Exception as ex:
                self.log.exception(ex)

        self.ws.orderbook_stream(depth=50, symbol=pair, callback=handle_ticker)

        while not stop_event.is_set():
            pass

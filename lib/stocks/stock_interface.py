import logging
import functools
import queue
import threading
from typing import List

from concurrent.futures import ThreadPoolExecutor

from lib.stocks.db_map.map_interface import (IMap, ITicker, ICandle, ICandleTicker, IOrderBook,
                                             IPosition, IInstrumentInfo)
from lib.rwlock import RWLock


class StockNotification:
    NOTIFICATIONS = {
        "BLUE",
        "GREEN"
    }

    def __init__(self, kind: str, data: dict = None):
        self.kind = kind
        if kind not in self.NOTIFICATIONS:
            raise ValueError(
                f"notification '{kind}' is not exist in available_notifications: {self.NOTIFICATIONS}")
        self.data = data

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, value):
        self._data = value


def atomic_in_threads(rwlock: RWLock, side):
    """
    Decorator

    ATOMIC - Make `func` atomic relatively to OBEYs and other `func` in different threads

    OBEY - `func` will wait until all ATOMICs will be finished

    :param side: OBEY/ATOMIC
    :param rwlock: RWLock() object. Should be the same for one group of readers/writers
    """
    def inner(func):
        def _decorator(*args, **kwargs):
            try:
                if side == "ATOMIC":
                    with rwlock.w_locked():
                        response = func(*args, **kwargs)
                if side == "OBEY":
                    with rwlock.r_locked():
                        response = func(*args, **kwargs)
            except Exception as ex:
                logging.getLogger().exception(ex)
            else:
                return response
        return functools.wraps(func)(_decorator)
    return inner


class IStock:
    """
        Methods return data according to the implementation of IMap (DB names)

        only trading on derivatives (futures)!
    """

    GET_FACT_EARN_NET_rwlock = RWLock()

    def __init__(self, map: IMap):
        self.log_stock = None  # logging.getLogger(__name__)
        # for example to notify that the order has been fulfilled
        self.notifications_queue = queue.Queue()
        self.map = map
        self.thread_pool_executor = ThreadPoolExecutor(max_workers=None)
        self._instrument_infos = {}

    def stream_decorator(func):
        """
        Makes the function non-blocking
        """

        def wrapper(self, handler, handler_kwargs, stop_event, **kwargs):
            handler_kwargs = {} if handler_kwargs is None else handler_kwargs
            future = self.thread_pool_executor.submit(
                func,
                self=self,
                handler=handler,
                handler_kwargs=handler_kwargs,
                stop_event=stop_event,
                **kwargs
            )

        return wrapper

    stream_decorator = staticmethod(stream_decorator)

    def get_min_order_qty_price(self, pair, verbose=False):
        """
        By market

        Get minimum allowed qty in coins and equivalent in money for creating the order

        :param pair:
        :param verbose:
        :return: {"qty": min_in_qty, "money": min_in_money}
        """
        raise NotImplemented()

    def get_USDT_deposit(self):
        """
        Return USDT wallet deposit

        :return: float
        """
        raise NotImplemented()

    def get_funding_rate(self, pair, verbose=False):
        """
        Returns the funding rate at the current time

        :param pair:
        :return: float
        """
        raise NotImplemented()

    def get_instrument_info(self, pair, verbose=False) -> IInstrumentInfo:
        """
        Instrument information

        Store the requested info in self._instrument_infos

        :param pair:
        :return: IInstrumentInfo()
        """
        raise NotImplemented()

    @atomic_in_threads(GET_FACT_EARN_NET_rwlock, "OBEY")
    def open_modify_SHORT_LONG(self, side, pair, amount_money_add=None, stopLoss=None, takeProfit=None):
        """
        By market

        amount_money_add > 0: To close the position use `close_SHORT_LONG()` (recommended) or open
                                                                        the opposite side position

        If the current pair already has the position size - the amount will be added to the current one

        If stopLoss or/and takeProfit provided - they will be changed to the provided values

        Immediate or Cancel (IOC)
        The order must be filled immediately at the order limit price or better. If the order
        cannot be filled immediately, the unfilled contracts will be canceled. IOC is usually
        used to avoid large orders being executed at a price that deviates from the ideal price.
        With this set, the contracts that fail to trade at the specified price will be canceled.

        :param side: "SHORT"/"LONG"
        :param pair:
        :param amount_money_add: in fiat (USDT)
        :param stopLoss:
        :param takeProfit:
        :return: orderId
        """
        raise NotImplemented()

    @atomic_in_threads(GET_FACT_EARN_NET_rwlock, "ATOMIC")
    def close_SHORT_LONG(self, pair, amount_percent=100) -> float:
        """
        By market

        if amount_percent=100 - all the qty (coins) will be closed by market price

        Good till canceled (GTC)
        The order will remain valid until it is fully executed or manually canceled by the trader.
        GTC is suitable for traders who are willing to wait for all contracts to be completed at
        a specified price and can flexibly cancel unconcluded contracts at any time.

        :return: earn_fact_net = balance_end - balance_init
        """
        raise NotImplemented()

    def formula_AEP(self, entry_qty_price_list: list):
        """
        Calculate Average entry price of the position

        :param entry_qty_price_list: [ (Quantity1 x Price1) + (Quantity2 x Price2)...]

        :return:
        """
        raise NotImplemented()

    def formula_profit_loss(self, pair, side, average_entry_price_usdt, last_traded_price, qty,
                            margin_leverage_pair, margin_leverage_pair_max, funding_rate, verbose=False):
        """
        Calculate the profit/losses (what you get in wallet) if close position by market

        :return: {
                    "Unrealized_PL_Money": float,
                    "ROI_percent": float,
                    "Closed_PL_Money": float
                }
        """
        raise NotImplemented()

    def get_history_tohlcv(self, pair, interval, start, end=None) -> List[ICandle]:
        """

        :param pair: "BTCUSDT"
        :param interval: "5", "10", "30", ...
        :param start: "16.09.2024 19:00:00,00" - early date
        :param end: "16.09.2024 19:00:00,00" or None for the current date - later date

        :return [
                    ICandle ,
                    ...
                ]
        """
        raise NotImplemented()

    def get_ticker(self, pair) -> ITicker:
        """
        for tests only. use stream for prod

        :param pair:
        :return: ITicker
        """
        raise NotImplemented()

    def get_all_pairs(self) -> List[str]:
        """
        get all available pairs

        :return:
        """
        raise NotImplemented()

    def get_position_status(self, pair) -> IPosition:
        """
        for tests and some internal only. use stream for prod

        :return: IPosition
        """
        raise NotImplemented()

    @stream_decorator
    def stream_ticker(self, handler: callable, handler_kwargs: dict, stop_event: threading.Event,
                      pair) -> None:
        """
        :param pair: "BTCUSDT"
        :param stop_event: to stop streaming
        :return to `handler` ITicker
        """
        raise NotImplemented()

    @stream_decorator
    def stream_tohlcv(self, handler: callable, handler_kwargs: dict, stop_event: threading.Event,
                      pair, interval) -> None:
        """

        :param pair: "BTCUSDT"
        :param stop_event: to stop streaming
        :return to `handler` ICandleTicker
        """
        raise NotImplemented()

    @stream_decorator
    def stream_order_book(self, handler: callable, handler_kwargs: dict, stop_event: threading.Event,
                          pair) -> None:
        """

        :param pair: "BTCUSDT"
        :param stop_event: to stop streaming
        :return to `handler` IOrderBook
        """
        raise NotImplemented()

    @stream_decorator
    def stream_position_status(self, handler: callable, handler_kwargs: dict, stop_event: threading.Event):
        """

        Position
        Subscribe to the position stream to see changes to your position data in real-time.

        :param stop_event: to stop streaming
        :return to `handler` IPosition
        """
        raise NotImplemented()

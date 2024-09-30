import logging
import queue
import threading
from concurrent.futures import ThreadPoolExecutor

from lib.stocks.db_map.map_interface import IMap


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


class IStock:
    """
        Methods return data according to the implementation of IMap (DB names)
    """

    def __init__(self, map: IMap):
        self.log = logging.getLogger(__name__)
        # for example to notify that the order has been fulfilled
        self.notifications_queue = queue.Queue()
        self.map = map
        self.thread_pool_executor = ThreadPoolExecutor(max_workers=None)

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


    def open_SHORT(self, uid, price, amount, stopLimit, takeProfit, limit=None):
        raise NotImplemented()

    def open_LONG(self, uid, price, amount, stopLimit, takeProfit, limit=None):
        raise NotImplemented()

    def close_SHORT_LONG(self, uid, limit=None):
        raise NotImplemented()

    def get_history_tohlcv(self, pair, interval, start, end=None):
        """

        :return: interator of dicts IMap.candle
        """
        raise NotImplemented()

    @stream_decorator
    def stream_ticker(self, handler: callable, handler_kwargs: dict, stop_event: threading.Event,
                      pair):
        """

        :param pair:
        :param stop_event: to stop streaming
        :return: interator of dicts IMap.ticker
        """
        raise NotImplemented()

    @stream_decorator
    def stream_tohlcv(self, handler: callable, handler_kwargs: dict, stop_event: threading.Event,
                      pair, interval):
        """

        :param pair:
        :param stop_event: to stop streaming
        :return: interator
        """
        raise NotImplemented()

    @stream_decorator
    def stream_order_book(self, handler: callable, handler_kwargs: dict, stop_event: threading.Event,
                          pair):
        """

        :param pair:
        :param stop_event: to stop streaming
        :return: interator of dicts IMap.order_book
        """
        raise NotImplemented()

    @stream_decorator
    def stream_order_status(self, handler: callable, handler_kwargs: dict, stop_event: threading.Event,
                            pair):
        """

        :param pair:
        :param stop_event: to stop streaming
        :return: interator
        """
        raise NotImplemented()


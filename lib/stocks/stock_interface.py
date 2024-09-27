import queue
import threading

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
        # for example to notify that the order has been fulfilled
        self.notifications_queue = queue.Queue()
        self.map = map

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

    # TODO create stream decorator
    def stream_ticker(self, pair, stop_event: threading.Event):
        """

        :param pair:
        :param stop_event: to stop streaming
        :return: interator of dicts IMap.ticker
        """
        raise NotImplemented()

    def stream_tohlcv(self, pair, interval, stop_event: threading.Event):
        """

        To stream requested interval in iterator

        :param pair:
        :param stop_event: to stop streaming
        :return: interator
        """
        raise NotImplemented()

    def stream_order_book(self, pair, stop_event: threading.Event):
        """

        :param pair:
        :param stop_event: to stop streaming
        :return: interator of dicts IMap.order_book
        """
        raise NotImplemented()

    def stream_order_status(self, pair, stop_event: threading.Event):
        """

        :param pair:
        :param stop_event: to stop streaming
        :return: interator
        """
        raise NotImplemented()


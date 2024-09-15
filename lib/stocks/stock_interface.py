import queue
import threading


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
    # TODO: Create unified schema for different stocks

    def __init__(self):
        # for example to notify that the order has been fulfilled
        self.notifications_queue = queue.Queue()

    def open_SHORT(self, uid, price, amount, stopLimit, takeProfit, limit=None):
        raise NotImplemented()

    def open_LONG(self, uid, price, amount, stopLimit, takeProfit, limit=None):
        raise NotImplemented()

    def close_SHORT_LONG(self, uid, limit=None):
        raise NotImplemented()

    def get_history_tohlcv(self, pair, interval, start, end=None):
        raise NotImplemented()

    def stream_ticker(self, pair, handler: callable, stop_event: threading.Event):
        """

        :param pair:
        :param handler: handler(message)
        :param stop_event: to stop streaming
        :return:
        """
        raise NotImplemented()
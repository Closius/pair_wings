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

        :param pair: "BTCUSDT"
        :param interval: "5", "10", "30", ...
        :param start: "16.09.2024 19:00:00,00" - early date
        :param end: "16.09.2024 19:00:00,00" or None for the current date - later date

        :return [
                    {
                        'Time': datetime.datetime(2024, 9, 16, 19, 15),
                        'Open': '57566.6',
                        'High': '57718.8',
                        'Low': '57535.1',
                        'Close': '57569.7',
                        'Volume': '614.993',
                        'Turnover': '35447184.1698'
                    },
                    ...
                ]
        """
        raise NotImplemented()

    @stream_decorator
    def stream_ticker(self, handler: callable, handler_kwargs: dict, stop_event: threading.Event,
                      pair):
        """
        :param pair: "BTCUSDT"
        :param stop_event: to stop streaming
        :return to `handler` {
                    'Time': datetime.datetime(2024, 10, 2, 22, 54, 17, 928000),
                    'MarkPrice': '3259.94',
                    'Ask1Size': '0.155',
                    'Bid1Size': '4199.144',
                    'OpenInterest': '1224249.628',
                    'OpenInterestValue': '3990980332.30'
                 }
        """
        raise NotImplemented()

    @stream_decorator
    def stream_tohlcv(self, handler: callable, handler_kwargs: dict, stop_event: threading.Event,
                      pair, interval):
        """

        :param pair: "BTCUSDT"
        :param stop_event: to stop streaming
        :return to `handler` {
                    'Time': datetime.datetime(2024, 10, 2, 23, 20, 41, 655000),
                    'Start': datetime.datetime(2024, 10, 2, 23, 20),
                    'End': datetime.datetime(2024, 10, 2, 23, 24, 59, 999000),
                    'Open': '55239.6',
                    'High': '55440',
                    'Low': '53750',
                    'Close': '55440',
                    'Volume': '2382.393',
                    'Turnover': '132078946.7517'
                }
        """
        raise NotImplemented()

    @stream_decorator
    def stream_order_book(self, handler: callable, handler_kwargs: dict, stop_event: threading.Event,
                          pair):
        """

        :param pair: "BTCUSDT"
        :param stop_event: to stop streaming
        :return to `handler` {
                    'Time': datetime.datetime(2024, 10, 2, 23, 20, 39, 873000),
                    'Asks': np.array(shape=(50, 2)),  # [price, volume], order: price lower -> higher
                    'Bids': np.array(shape=(50, 2)),  # [price, volume], order: price higher -> lower
                }
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


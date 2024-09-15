import queue

import pandas as pd

from lib.stocks.stock_interface import IStock, StockNotification


class IStrategy:

    def __init__(self, stock_model: IStock, uid: str, pair: str, history_tohlcv: pd.DataFrame):
        """

        :param stock_model: provides actual market actions like open/close SHORT/LONG
        :param uid:
        :param pair:
        :param history_tohlcv: ["Time", "Open", "High", "Low", "Close", "Volume"] "Time" is index
        """
        self.stock = stock_model
        self.uid = uid
        self.pair = pair
        self.tohlcv = history_tohlcv
        self.instruments: dict = {}  # like technical indicators and so on
        self.trading_info: dict = {}  # trading information: efficiency, profit and so on
        self._stock_notifications_callables: dict = {}

    def process_stock_notifications(self):
        """
        This method should be called in the same thread to avoid concurrency problems.
        For example if the Stock (self.stock) is generated a notification "the order has been executed"
        and the Strategy is dependent on it, then in a parallel mode it may overlap with
        the current calculation of make_decision() or something else which may lead to unpredicted behavior
        """
        while True:
            try:
                notification = self.stock.notifications_queue.get(block=False)
                self._stock_notifications_callables[notification](**notification.data)
            except queue.Empty:
                break

    def subscribe_on_stock_notifications(self, func: callable, kwargs: dict, event_name: str):
        if event_name not in StockNotification.NOTIFICATIONS:
            raise ValueError(f"notification {event_name} is not exist in used Stock. "
                             f"Available notifications: {StockNotification.NOTIFICATIONS}")
        self._stock_notifications_callables[event_name] = func(**kwargs)

    def add_update_new_data(self, tohlcv: pd.DataFrame):
        if self.tohlcv.tail(1).index.item() in tohlcv.index:
            self.tohlcv.update(tohlcv)
        else:
            self.tohlcv = pd.concat([self.tohlcv, tohlcv])
        self.update_instruments()

    def update_instruments(self):
        """
        Update instruments like technical indicators and so on
        """
        raise NotImplemented()

    def update_trade_info(self):
        """
        Update trading information: efficiency, profit and so on
        """
        raise NotImplemented()

    def make_decision(self):
        raise NotImplemented()
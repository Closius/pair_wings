from lib.stocks.stock_interface import IStock
from lib import utils
from lib.database import DB


class StockTestDB(IStock):

    def __init__(self, db_filepath):
        self.db = DB(db_filepath)
        super().__init__()

    def open_SHORT(self, uid, price, amount, stopLimit, takeProfit, limit=None):
        raise NotImplemented()

    def open_LONG(self, uid, price, amount, stopLimit, takeProfit, limit=None):
        raise NotImplemented()

    def close_SHORT_LONG(self, uid, limit=None):
        raise NotImplemented()

    def get_history_tohlcv(self, pair, interval, start, end=None):
        raise NotImplemented()

    def stream_ticker(self, pair, handler: callable, stop_event):
        """

        :param pair:
        :param handler: handler(message)
        :param stop_event: to stop streaming
        :return:
        """
        raise NotImplemented()
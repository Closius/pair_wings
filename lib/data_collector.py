import logging

from lib import utils
from lib import database

from lib.stocks.stock_interface import IStock

from lib.schema import Ticker, CandleTicker, OrderBook


class DataCollector:

    def __init__(self, stock: IStock, filepath):
        self.log = logging.getLogger(__name__)
        self.db_filepath = filepath
        self.stock = stock
        self.log.info(f"DataCollector {self.db_filepath}")
        self.db = database.DB(self.db_filepath)

    def collect_stream_tickers(self, pair, stop_event, recreate=False):
        self.log.info(f"collect_tickers {pair}")
        self.db.create_ticker_table(pair, recreate)

        def handler(message: Ticker):
            _db = database.DB(self.db_filepath)
            _db.insert_ticker(
                pair=pair,
                obj=message
            )
            self.log.info(f'ticker {utils.datetime_to_text(message.Time)} | '
                          f'{message.MarkPrice}')

        self.stock.stream_ticker(handler=handler, handler_kwargs={}, stop_event=stop_event,
                                 pair=pair)

    def collect_history_candles(self, pair, interval, start_utc, end_utc=None, recreate=False):
        """

        :param pair:
        :param interval: 1,3,5,15,30,60,120,240,360,720,D,M,W
        :param start_utc: '20.12.2016 09:38:42,76'
        :param end_utc: '20.12.2016 09:38:42,76'
        :param recreate:
        :return:
        """
        self.log.info(f"collect_candles {pair}")
        self.db.create_candle_table(pair, recreate)

        for candle in self.stock.get_history_tohlcv(pair, interval, start_utc, end_utc, verbose=True):
            self.db.insert_candle(
                pair=pair,
                obj=candle
            )

        self.log.info(f"collect_candles Finished.")

    def collect_stream_candles_ticker(self, pair, interval, stop_event, recreate=False):
        self.log.info(f"collect_stream_candles_ticker {pair} {interval}")
        self.db.create_candle_ticker_table(pair, interval, recreate)

        def handler(message: CandleTicker):
            _db = database.DB(self.db_filepath)
            _db.insert_candle_ticker(
                pair=pair,
                interval=interval,
                obj=message
            )
            self.log.info(f'candle {utils.datetime_to_text(message.Time)} | '
                          f'{message.Close}')

        self.stock.stream_tohlcv(handler=handler, handler_kwargs={}, stop_event=stop_event,
                                 pair=pair, interval=interval)

    def collect_stream_order_book(self, pair, stop_event, recreate=False):
        self.log.info(f"collect_stream_order_book {pair}")
        self.db.create_order_book_table(pair, recreate)

        def handler(message: OrderBook):
            _db = database.DB(self.db_filepath)
            _db.insert_order_book(
                pair=pair,
                obj=message
            )
            self.log.info(f'order book {utils.datetime_to_text(message.Time)}')

        self.stock.stream_order_book(handler=handler, handler_kwargs={}, stop_event=stop_event,
                                 pair=pair)

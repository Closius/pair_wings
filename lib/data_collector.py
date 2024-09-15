import json5
import logging
import threading
import concurrent.futures

from lib import utils
from lib import database

from lib.stocks.stock_interface import IStock


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

        def handle_ticker(message):
            try:
                self.db = database.DB(self.db_filepath)
                attrs = {x[0]: message["data"][x[0]] for x in database.DB.TICKER_COLUMNS}
                self.db.insert_ticker(
                    pair=pair,
                    time=message["ts"],
                    **attrs
                )
                self.log.info(f'{utils.ts_to_text(message["ts"])} | {message["data"]["markPrice"]}')

            except Exception as ex:
                logging.getLogger(__name__).exception(ex)

        self.stock.stream_ticker(pair, handle_ticker, stop_event)

        self.log.info(f"collect_tickers Finished.")

    def collect_history_candles(self, pair, interval, start, end=None, recreate=False):
        """

        :param pair:
        :param interval:
        :param start: timestamp in ms
        :param end: timestamp in ms
        :param recreate:
        :return:
        """
        self.log.info(f"collect_candles {pair}")
        self.db.create_candle_table(pair, recreate)

        for candle in self.stock.get_history_tohlcv(pair, interval, start, end):
            self.log.info(json5.dumps(candle, indent=4))
            attrs = {x[0]: candle[database.DB.CANDLE_COLUMNS.index(x)] for x in database.DB.CANDLE_COLUMNS}
            self.db.insert_candles(
                pair=pair,
                **attrs
            )

        self.log.info(f"collect_candles Finished.")


def collect_stream_tickers(stock: IStock, filepath, pair, recreate):
    def _func(_stock, _filepath, _pair, _recreate, _stop_event):
        try:
            dc = DataCollector(_stock, _filepath)
            dc.collect_stream_tickers(_pair, _stop_event, _recreate)
        except Exception as ex:
            logging.getLogger(__name__).exception(ex)
    log = logging.getLogger(__name__)
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        event = threading.Event()
        future = executor.submit(
            _func,
            _stock=stock,
            _filepath=filepath,
            _pair=pair,
            _recreate=recreate,
            _stop_event=event,
        )
        log.info("==========================")
        log.info("Press Enter to Stop collection")
        input()
        event.set()
        log.info("Interrupted")
        try:
            future.result()
        except Exception as exc:
            log.exception(exc)


def collect_history_candles(stock: IStock, filepath, recreate, pair, interval, start, end=None):
    """

    :param filepath:
    :param pair:
    :param interval: 1,3,5,15,30,60,120,240,360,720,D,M,W
    :param start: '20.12.2016 09:38:42,76'
    :param end: '20.12.2016 09:38:42,76'
    :param recreate:
    :return:
    """
    try:
        dc = DataCollector(stock, filepath)
        dc.collect_history_candles(pair, interval, start, end, recreate)
    except Exception as ex:
        logging.getLogger(__name__).exception(ex)
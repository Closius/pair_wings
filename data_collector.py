import json5
import sqlite3
import logging

import pandas as pd

from pybit.unified_trading import WebSocket
from pybit.unified_trading import HTTP

import utils


class DB:
    _TIME = ("Time", "TIMESTAMP")
    TICKER_COLUMNS = [
        ("markPrice", "REAL"),
        ("ask1Size", "REAL"),
        ("bid1Size", "REAL"),
        ("openInterest", "REAL"),
        ("openInterestValue", "REAL")
    ]

    CANDLE_COLUMNS = [
        ("startTime", "TIMESTAMP", "Time"),
        ("openPrice", "REAL", "Open"),
        ("highPrice", "REAL", "High"),
        ("lowPrice", "REAL", "Low"),
        ("closePrice", "REAL", "Close"),
        ("volume", "REAL", "Volume"),
        ("turnover", "REAL", "Turnover"),
    ]

    def __init__(self, filepath):
        self.filepath = filepath
        self.con = sqlite3.connect(self.filepath)
        self.cur = self.con.cursor()

    def create_ticker_table(self, pair, recreate=False):
        if recreate:
            self.cur.execute(
                f"""
                DROP TABLE IF EXISTS tickers_{pair}
            """
            )
        cols = ",".join([f"{x[0]} {x[1]}" for x in self.TICKER_COLUMNS])
        self.cur.execute(
            f"""
            CREATE TABLE IF NOT EXISTS tickers_{pair}
                ({self._TIME[0]} {self._TIME[1]} UNIQUE, 
                {cols})
        """
        )

    def create_candle_table(self, pair, recreate=False):
        if recreate:
            self.cur.execute(
                f"""
                DROP TABLE IF EXISTS candles_{pair}
            """
            )
        cols = ",".join([f"{x[0]} {x[1]}" for x in self.CANDLE_COLUMNS])
        self.cur.execute(
            f"""
            CREATE TABLE IF NOT EXISTS candles_{pair}
                ({cols})
        """
        )

    def insert_ticker_table(self, pair, time, **kwargs):

        cols = ",".join([f"{kwargs[x[0]]}" for x in self.TICKER_COLUMNS])
        self.cur.execute(
            f"""
            INSERT INTO tickers_{pair} VALUES
                ({time}, {cols})
        """
        )
        self.con.commit()

    def insert_candle_table(self, pair, **kwargs):

        cols = ",".join([f"{kwargs[x[0]]}" for x in self.CANDLE_COLUMNS])
        self.cur.execute(
            f"""
            INSERT INTO candles_{pair} VALUES
                ({cols})
        """
        )
        self.con.commit()

    def read_ticker_table(self, pair, t_start=None, t_end=None):
        if t_start and t_end:
            res = self.cur.execute(
                f"""SELECT * FROM tickers_{pair} 
                WHERE {self._TIME[0]} >= {t_start} AND time <= {t_end}
                ORDER BY {self._TIME[0]}"""
            )
        elif t_start:
            res = self.cur.execute(
                f"""SELECT * FROM tickers_{pair} 
                WHERE {self._TIME[0]} >= {t_start}
                ORDER BY {self._TIME[0]}"""
            )
        else:
            res = self.cur.execute(
                f"""SELECT * FROM tickers_{pair} 
                ORDER BY {self._TIME[0]}"""
            )
        df = pd.DataFrame(res.fetchall(), columns=[self._TIME[0]] + [x[0] for x in self.TICKER_COLUMNS])
        df[self._TIME[0]] = pd.to_datetime(df[self._TIME[0]].astype(int), unit='ms')
        df.index = pd.DatetimeIndex(df[self._TIME[0]])
        # df.drop(columns=[self._TIME[0]])
        return df

    def read_candle_table(self, pair, t_start=None, t_end=None):
        if t_start and t_end:
            res = self.cur.execute(
                f"""SELECT * FROM candles_{pair} 
                WHERE {self.CANDLE_COLUMNS[0][0]} >= {t_start} AND time <= {t_end}
                ORDER BY {self.CANDLE_COLUMNS[0][0]}"""
            )
        elif t_start:
            res = self.cur.execute(
                f"""SELECT * FROM candles_{pair} 
                WHERE {self.CANDLE_COLUMNS[0][0]} >= {t_start}
                ORDER BY {self.CANDLE_COLUMNS[0][0]}"""
            )
        else:
            res = self.cur.execute(
                f"""SELECT * FROM candles_{pair} 
                ORDER BY {self.CANDLE_COLUMNS[0][0]}"""
            )
        df = pd.DataFrame(res.fetchall(), columns=[x[2] for x in self.CANDLE_COLUMNS])
        df[self.CANDLE_COLUMNS[0][2]] = pd.to_datetime(df[self.CANDLE_COLUMNS[0][2]].astype(int), unit='ms')
        df.index = pd.DatetimeIndex(df[self.CANDLE_COLUMNS[0][2]])
        # df.drop(columns=[self.CANDLE_COLUMNS[0][2]])
        return df

class DataCollector:

    def __init__(self, filepath, stop_event):
        self.log = logging.getLogger(__name__)
        self.db_filepath = filepath
        self.log.info(f"DataCollector {self.db_filepath}")
        self.db = DB(self.db_filepath)
        self.http = HTTP(demo=True)
        self.stop_event = stop_event

    def collect_tickers(self, pair, recreate=False):
        self.log.info(f"collect_tickers {pair}")
        self.db.create_ticker_table(pair, recreate)

        self.ws = WebSocket(
            testnet=True,  # testnet gives wrong values! at least on HTTP
            channel_type="linear"
        )

        def handle_ticker(message):
            try:
                self.db = DB(self.db_filepath)
                attrs = {x[0]: message["data"][x[0]] for x in DB.TICKER_COLUMNS}
                self.db.insert_ticker_table(
                    pair=pair,
                    time=message["ts"],
                    **attrs
                )
                self.log.info(f'{utils.ts_to_text(message["ts"])} | {message["data"]["markPrice"]}')

            except Exception as ex:
                logging.getLogger(__name__).exception(ex)

        self.ws.ticker_stream(pair, handle_ticker)

        while not self.stop_event.is_set():
            pass

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

        kargs = {
            "category": "linear",
            "symbol": pair,
            "interval": interval,
            "start": utils.datetime_text_to_ts(start),
        }
        if end:
            kargs["end"] = utils.datetime_text_to_ts(end)

        for candle in self.http.get_kline(**kargs)["result"]["list"]:
            self.log.info(json5.dumps(candle, indent=4))
            attrs = {x[0]: candle[DB.CANDLE_COLUMNS.index(x)] for x in DB.CANDLE_COLUMNS}
            self.db.insert_candle_table(
                pair=pair,
                **attrs
            )

        self.log.info(f"collect_candles Finished.")


def collect_tickers(filepath, pair, recreate, stop_event):
    try:
        dc = DataCollector(filepath, stop_event)
        dc.collect_tickers(pair, recreate)
    except Exception as ex:
        logging.getLogger(__name__).exception(ex)

def collect_history_candles(filepath, recreate, pair, interval, start, end=None):
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
        dc = DataCollector(filepath, stop_event=None)
        dc.collect_history_candles(pair, interval, start, end, recreate)
    except Exception as ex:
        logging.getLogger(__name__).exception(ex)
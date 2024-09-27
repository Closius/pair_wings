import logging
import sqlite3
import numpy as np
import io

import pandas as pd

from lib.stocks.db_map.map_interface import IMap, _NDARRAY_DB_TYPE
from lib import utils


def numpy_to_sqlite(arr):
    """
    http://stackoverflow.com/a/31312102/190597 (SoulNibbler)
    """
    out = io.BytesIO()
    np.save(out, arr)
    out.seek(0)
    return sqlite3.Binary(out.read())


def sqlite_to_numpy(text):
    out = io.BytesIO(text)
    out.seek(0)
    return np.load(out)


class DB:
    def __init__(self, filepath, map: IMap):
        # Converts np.array to TEXT when inserting
        sqlite3.register_adapter(np.ndarray, numpy_to_sqlite)
        # Converts TEXT to np.array when selecting
        sqlite3.register_converter(_NDARRAY_DB_TYPE, sqlite_to_numpy)

        self.log = logging.getLogger(__name__)
        self.filepath = filepath
        self.map = map
        self.con = sqlite3.connect(self.filepath, detect_types=sqlite3.PARSE_DECLTYPES)
        self.cur = self.con.cursor()

    def create_ticker_table(self, pair, recreate=False):
        if recreate:
            self.cur.execute(
                f"""
                DROP TABLE IF EXISTS tickers_{pair}
            """
            )
        self.cur.execute(
            f"""
            CREATE TABLE IF NOT EXISTS tickers_{pair}
                ({self.map.ticker.get_names_types_for_DB()})
        """
        )

    def create_candle_table(self, pair, recreate=False):
        """
        A historical candles table. each row - the finished candle for current period
        """
        if recreate:
            self.cur.execute(
                f"""
                DROP TABLE IF EXISTS candles_{pair}
            """
            )
        self.cur.execute(
            f"""
            CREATE TABLE IF NOT EXISTS candles_{pair}
                ({self.map.candle.get_names_types_for_DB()})
        """
        )

    def create_candle_ticker_table(self, pair, interval, recreate=False):
        """
        Candles which are collected from the database as fast as they receive FROM THE STREAMING
        """
        if recreate:
            self.cur.execute(
                f"""
                DROP TABLE IF EXISTS candles_ticker_{pair}_{interval}
            """
            )
        self.cur.execute(
            f"""
            CREATE TABLE IF NOT EXISTS candles_ticker_{pair}_{interval}
                ({self.map.candle_ticker.get_names_types_for_DB()})
        """
        )

    def create_order_book_table(self, pair, recreate=False):
        if recreate:
            self.cur.execute(
                f"""
                DROP TABLE IF EXISTS order_book_{pair}
            """
            )
        self.cur.execute(
            f"""
            CREATE TABLE IF NOT EXISTS order_book_{pair}
                ({self.map.order_book.get_names_types_for_DB()})
        """
        )

    def insert_ticker(self, pair, **kwargs):
        # preserve the order as in Map and DB
        cols = [f"{kwargs[x]}" for x in self.map.ticker.get_db_names()]
        q = ",".join(["?"] * len(self.map.ticker.get_db_names()))
        self.cur.execute(
            f"""
            INSERT INTO tickers_{pair} VALUES
                ({q})
        """, cols
        )
        self.con.commit()

    def insert_candle(self, pair, **kwargs):
        """
        Insert into the historical candles table. each row - the finished candle for current period
        """
        # preserve the order as in Map and DB
        cols = [kwargs[x] for x in self.map.candle.get_db_names()]
        q = ",".join(["?"] * len(self.map.candle.get_db_names()))
        self.cur.execute(
            f"""
            INSERT INTO candles_{pair} VALUES
                ({q})
        """, cols
        )
        self.con.commit()

    def insert_candle_ticker(self, pair, interval, **kwargs):
        # preserve the order as in Map and DB
        cols = [f"{kwargs[x]}" for x in self.map.candle_ticker.get_db_names()]
        q = ",".join(["?"] * len(self.map.candle_ticker.get_db_names()))
        self.cur.execute(
            f"""
            INSERT INTO candles_ticker_{pair}_{interval} VALUES
                ({q})
        """, cols
        )
        self.con.commit()

    def insert_order_book(self, pair, **kwargs):
        # preserve the order as in Map and DB
        cols_order = []
        for db_name in self.map.order_book.get_db_names():
            cols_order.append(kwargs[db_name])
        q = ",".join(["?"]*len(self.map.order_book.get_db_names()))
        self.cur.execute(f"""
            INSERT INTO order_book_{pair} VALUES
                ({q})
        """, cols_order)
        self.con.commit()

    def read_ticker_table(self, pair, t_start=None, t_end=None):
        if t_start and t_end:
            res = self.cur.execute(
                f"""SELECT * FROM tickers_{pair} 
                WHERE {self.map.ticker.Time.db_name} >= {t_start} AND time <= {t_end}
                ORDER BY {self.map.ticker.Time.db_name}"""
            )
        elif t_start:
            res = self.cur.execute(
                f"""SELECT * FROM tickers_{pair} 
                WHERE {self.map.ticker.Time.db_name} >= {t_start}
                ORDER BY {self.map.ticker.Time.db_name}"""
            )
        else:
            res = self.cur.execute(
                f"""SELECT * FROM tickers_{pair} 
                ORDER BY {self.map.ticker.Time.db_name}"""
            )
        df = pd.DataFrame(res.fetchall(), columns=self.map.ticker.get_db_names())
        df[self.map.ticker.Time.db_name] = pd.to_datetime(df[self.map.ticker.Time.db_name], unit='ms')
        df.index = pd.DatetimeIndex(df[self.map.ticker.Time.db_name])
        # df.drop(columns=[self.map.ticker.Time.db_name])
        return df

    def read_candle_table(self, pair, t_start=None, t_end=None):
        if t_start and t_end:
            res = self.cur.execute(
                f"""SELECT * FROM candles_{pair} 
                WHERE {self.map.candle.Time.db_name} >= {t_start} AND time <= {t_end}
                ORDER BY {self.map.candle.Time.db_name}"""
            )
        elif t_start:
            res = self.cur.execute(
                f"""SELECT * FROM candles_{pair} 
                WHERE {self.map.candle.Time.db_name} >= {t_start}
                ORDER BY {self.map.candle.Time.db_name}"""
            )
        else:
            res = self.cur.execute(
                f"""SELECT * FROM candles_{pair} 
                ORDER BY {self.map.candle.Time.db_name}"""
            )
        df = pd.DataFrame(res.fetchall(), columns=self.map.candle.get_db_names())
        df[self.map.candle.Time.db_name] = pd.to_datetime(df[self.map.candle.Time.db_name], unit='ms')
        df.index = pd.DatetimeIndex(df[self.map.candle.Time.db_name])
        # df.drop(columns=[self.map.candle.Time.db_name])
        return df

    def read_candle_ticker_table(self, pair, interval, t_start=None, t_end=None):
        if t_start and t_end:
            res = self.cur.execute(
                f"""SELECT * FROM candles_ticker_{pair}_{interval} 
                WHERE {self.map.candle_ticker.Time.db_name} >= {t_start} AND time <= {t_end}
                ORDER BY {self.map.candle_ticker.Time.db_name}"""
            )
        elif t_start:
            res = self.cur.execute(
                f"""SELECT * FROM candles_ticker_{pair}_{interval} 
                WHERE {self.map.candle_ticker.Time.db_name} >= {t_start}
                ORDER BY {self.map.candle_ticker.Time.db_name}"""
            )
        else:
            res = self.cur.execute(
                f"""SELECT * FROM candles_ticker_{pair}_{interval} 
                ORDER BY {self.map.candle_ticker.Time.db_name}"""
            )
        df = pd.DataFrame(res.fetchall(), columns=self.map.candle_ticker.get_db_names())
        df[self.map.candle_ticker.Time.db_name] = pd.to_datetime(df[self.map.candle_ticker.Time.db_name], unit='ms')
        df[self.map.candle_ticker.Start.db_name] = pd.to_datetime(df[self.map.candle_ticker.Start.db_name], unit='ms')
        df[self.map.candle_ticker.End.db_name] = pd.to_datetime(df[self.map.candle_ticker.End.db_name], unit='ms')
        df.index = pd.DatetimeIndex(df[self.map.candle_ticker.Time.db_name])
        # df.drop(columns=[self.map.order_book.Time.db_name])
        return df

    def read_order_book_table(self, pair, t_start=None, t_end=None):
        if t_start and t_end:
            res = self.cur.execute(
                f"""SELECT * FROM order_book_{pair} 
                WHERE {self.map.order_book.Time.db_name} >= {t_start} AND time <= {t_end}
                ORDER BY {self.map.order_book.Time.db_name}"""
            )
        elif t_start:
            res = self.cur.execute(
                f"""SELECT * FROM order_book_{pair} 
                WHERE {self.map.order_book.Time.db_name} >= {t_start}
                ORDER BY {self.map.order_book.Time.db_name}"""
            )
        else:
            res = self.cur.execute(
                f"""SELECT * FROM order_book_{pair} 
                ORDER BY {self.map.order_book.Time.db_name}"""
            )
        df = pd.DataFrame(res.fetchall(), columns=self.map.order_book.get_db_names())
        df[self.map.order_book.Time.db_name] = pd.to_datetime(df[self.map.order_book.Time.db_name], unit='ms')
        df.index = pd.DatetimeIndex(df[self.map.order_book.Time.db_name])
        # df.drop(columns=[self.map.order_book.Time.db_name])
        return df

import sqlite3

import pandas as pd

from lib.stocks.db_map.map_interface import IMap


class DB:
    def __init__(self, filepath, map: IMap):
        self.filepath = filepath
        self.map = map
        self.con = sqlite3.connect(self.filepath)
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

    def insert_ticker(self, pair, **kwargs):

        cols = ",".join([f"{kwargs[x]}" for x in self.map.ticker.get_db_names()])
        self.cur.execute(
            f"""
            INSERT INTO tickers_{pair} VALUES
                ({cols})
        """
        )
        self.con.commit()

    def insert_candles(self, pair, **kwargs):

        cols = ",".join([f"{kwargs[x]}" for x in self.map.candle.get_db_names()])
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
        df[self.map.ticker.Time.db_name] = pd.to_datetime(df[self.map.ticker.Time.db_name].astype(int), unit='ms')
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
        df[self.map.candle.Time.db_name] = pd.to_datetime(df[self.map.candle.Time.db_name].astype(int), unit='ms')
        df.index = pd.DatetimeIndex(df[self.map.candle.Time.db_name])
        # df.drop(columns=[self.map.candle.Time.db_name])
        return df

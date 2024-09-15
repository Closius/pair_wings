import sqlite3

import pandas as pd


class DB:
    # TODO: Create unified schema for different stocks
    #       maybe move to separate file which will be used by IStock and DB
    _TIME_TICKER_COLUMNS = ("Time", "TIMESTAMP")
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
                ({self._TIME_TICKER_COLUMNS[0]} {self._TIME_TICKER_COLUMNS[1]} UNIQUE, 
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

    def insert_ticker(self, pair, time, **kwargs):

        cols = ",".join([f"{kwargs[x[0]]}" for x in self.TICKER_COLUMNS])
        self.cur.execute(
            f"""
            INSERT INTO tickers_{pair} VALUES
                ({time}, {cols})
        """
        )
        self.con.commit()

    def insert_candles(self, pair, **kwargs):

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
                WHERE {self._TIME_TICKER_COLUMNS[0]} >= {t_start} AND time <= {t_end}
                ORDER BY {self._TIME_TICKER_COLUMNS[0]}"""
            )
        elif t_start:
            res = self.cur.execute(
                f"""SELECT * FROM tickers_{pair} 
                WHERE {self._TIME_TICKER_COLUMNS[0]} >= {t_start}
                ORDER BY {self._TIME_TICKER_COLUMNS[0]}"""
            )
        else:
            res = self.cur.execute(
                f"""SELECT * FROM tickers_{pair} 
                ORDER BY {self._TIME_TICKER_COLUMNS[0]}"""
            )
        df = pd.DataFrame(res.fetchall(), columns=[self._TIME_TICKER_COLUMNS[0]] + [x[0] for x in self.TICKER_COLUMNS])
        df[self._TIME_TICKER_COLUMNS[0]] = pd.to_datetime(df[self._TIME_TICKER_COLUMNS[0]].astype(int), unit='ms')
        df.index = pd.DatetimeIndex(df[self._TIME_TICKER_COLUMNS[0]])
        # df.drop(columns=[self._TIME_TICKER_COLUMNS[0]])
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

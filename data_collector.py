import time
import datetime
import sqlite3
import logging


class DB:

    def __init__(self, filepath):
        self.filpath = filepath
        self.con = sqlite3.connect(self.filpath)
        self.cur = self.con.cursor()

    def create_ticker_table(self, pair):
        """
                {
            retCode: 0,
            retMsg: "OK",
            result: {
                category: "linear",
                list: [
                    {
                        symbol: "BTCUSDT",
                        lastPrice: "59517.50",
                        indexPrice: "59549.45",
                        markPrice: "59517.40",
                        prevPrice24h: "58270.00",
                        price24hPcnt: "0.021408",
                        highPrice24h: "59950.00",
                        lowPrice24h: "57579.00",
                        prevPrice1h: "59594.50",
                        openInterest: "62334.104",
                        openInterestValue: "3709963801.41",
                        turnover24h: "7034735544.2336",
                        volume24h: "120263.7350",
                        fundingRate: "-0.0000418",
                        nextFundingTime: "1726272000000",
                        predictedDeliveryPrice: "",
                        basisRate: "",
                        deliveryFeeRate: "",
                        deliveryTime: "0",
                        ask1Size: "14.078",
                        bid1Price: "59517.40",
                        ask1Price: "59517.50",
                        bid1Size: "9.127",
                        basis: "",
                        preOpenPrice: "",
                        preQty: "",
                        curPreListingPhase: "",
                    },
                ],
            },
            retExtInfo: {},
            time: 1726252381456,
        }
                :return:
        """
        self.cur.execute(
            f"""
            CREATE TABLE IF NOT EXISTS tickers_{pair}
                (time TIMESTAMP UNIQUE, 
                markPrice REAL, 
                ask1Size REAL,
                bid1Size REAL,
                openInterest REAL, 
                openInterestValue REAL)
        """
        )

    def insert_ticker_table(
        self, pair, time, markPrice, ask1Size, bid1Size, openInterest, openInterestValue
    ):
        self.cur.execute(
            f"""
            INSERT INTO tickers_{pair} VALUES
                ({time}, {markPrice}, {ask1Size}, {bid1Size}, {openInterest}, {openInterestValue})
        """
        )
        self.con.commit()

    def read_ticker_table(self, pair, t_start, t_end):
        res = self.cur.execute(
            f"""SELECT * FROM tickers_{pair} 
            WHERE time <= {t_start} AND time >= {t_end}
            ORDER BY time"""
        )
        return res.fetchall()  # [(8.2,), (7.5,)]


class DataCollector:

    def __init__(self, session, filepath, stop_event):
        self.log = logging.getLogger(__name__)
        self.log.info(f"DataCollector {filepath}")
        self.db = DB(filepath)
        self.session = session
        self.stop_event = stop_event
        self.period = 0.001  # seconds

    def collect_tickers(self, pair):
        self.log.info(f"collect_tickers {pair} step: {self.period} seconds")
        self.db.create_ticker_table(pair)
        tickers = self.session.get_tickers(category="linear", symbol=pair)
        date = datetime.datetime.fromtimestamp(tickers["time"] / 1e3).strftime(
            "%d/%m/%Y %H:%M:%S:%f"
        )
        self.log.info(f"start time: {date}")
        while not self.stop_event.is_set():
            try:
                tickers = self.session.get_tickers(category="linear", symbol=pair)
                self.db.insert_ticker_table(
                    pair,
                    tickers["time"],
                    tickers["result"]["list"][0]["markPrice"],
                    tickers["result"]["list"][0]["ask1Size"],
                    tickers["result"]["list"][0]["bid1Size"],
                    tickers["result"]["list"][0]["openInterest"],
                    tickers["result"]["list"][0]["openInterestValue"],
                )
                date = datetime.datetime.fromtimestamp(tickers["time"] / 1e3).strftime(
                    "%d/%m/%Y %H:%M:%S:%f"
                )
                self.log.info(f'{date} | {tickers["result"]["list"][0]["markPrice"]}')
                time.sleep(self.period)
            except TimeoutError:
                continue

        self.log.info(f"collect_tickers Finished.")


def collect_tickers(session, filepath, pair, stop_event):
    try:
        dc = DataCollector(session, filepath, stop_event)
        dc.collect_tickers(pair)
    except Exception as ex:
        logging.getLogger(__name__).exception(ex)

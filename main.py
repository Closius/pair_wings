import os
import json5
import logging
import threading

from lib import data_show, data_collector

from lib.stocks.stock_bybit import StockBybit
from lib.stocks.db_map.map_bybit import MapBybit


def main():
    if os.path.exists("pybit.log"):
        os.remove("pybit.log")
    logging.basicConfig(
        filename="pybit.log",
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    logging.getLogger().addHandler(logging.StreamHandler())
    log = logging.getLogger(__name__)

    log.info("==========================")
    log.info("Choose your destiny:")
    log.info("1 - Collect streams: candle, ticker, order book")
    log.info("2 - Collect candles")
    log.info("3 - Show candles")
    log.info("4 - Read order books")
    log.info("5 - Read stream candles")
    log.info("6 - Quit")
    r = input()
    log.info(r)
    # stock = StockBybit(account_name="pair_wings_demo",
    #                    api_secrets_file="api_secret.json",
    #                    settings_file="settings.json")
    map = MapBybit()
    stock = StockBybit(map=map)
    db_filepath = "main.db"
    event = threading.Event()
    if r == "1":
        dc = data_collector.DataCollector(stock, db_filepath, map)
        dc.collect_stream_tickers(pair="BTCUSDT", stop_event=event, recreate=True)
        dc.collect_stream_candles_ticker(pair="BTCUSDT", interval="5", stop_event=event, recreate=True)
        dc.collect_stream_order_book(pair="BTCUSDT", stop_event=event, recreate=True)

        log.info("==========================")
        log.info("Press Enter to Stop collection")
        input()
        event.set()
        log.info("Interrupted")

    elif r == "2":
        dc = data_collector.DataCollector(stock, db_filepath, map)
        dc.collect_history_candles(pair="BTCUSDT", interval="5",
                                   start='16.09.2024 19:00:00,00',
                                   end=None,
                                   recreate=True)

    elif r == "3":
        data_show.draw_candles(db_filepath, pair="BTCUSDT", map=map)
    elif r == "4":
        data_show.read_order_book(db_filepath, pair="BTCUSDT", map=map)
    elif r == "5":
        data_show.read_stream_candles(db_filepath, pair="BTCUSDT", interval="5", map=map)

if __name__ == "__main__":
    main()

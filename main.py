import os
import json5
import logging

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
    log.info("1 - Collect tickers")
    log.info("2 - Collect order book")
    log.info("3 - Collect candles")
    log.info("4 - Show data")
    log.info("5 - Quit")
    r = input()
    log.info(r)
    # stock = StockBybit(account_name="pair_wings_demo",
    #                    api_secrets_file="api_secret.json",
    #                    settings_file="settings.json")
    map = MapBybit()
    stock = StockBybit(map=map)
    db_filepath = "main.db"
    if r == "1":
        data_collector.collect_stream_tickers(
            stock=stock,
            filepath=db_filepath,
            pair="BTCUSDT",
            recreate=True,
            map=map)

    if r == "2":
        data_collector.collect_stream_order_book(
            stock=stock,
            filepath=db_filepath,
            pair="BTCUSDT",
            recreate=True,
            map=map)

    elif r == "3":
        data_collector.collect_history_candles(
            stock=stock,
            filepath=db_filepath,
            recreate=True,
            pair="BTCUSDT",
            interval="5",
            start='16.09.2024 19:00:00,00',
            map=map)
    elif r == "4":
        data_show.draw_candles(db_filepath, pair="BTCUSDT", map=map)


if __name__ == "__main__":
    main()

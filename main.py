import os
import json5
import logging

from lib import data_show, data_collector

from lib.stocks.stock_bybit import StockBybit


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
    log.info("2 - Collect candles")
    log.info("3 - Show data")
    log.info("4 - Quit")
    r = input()
    log.info(r)
    # stock = StockBybit(account_name="pair_wings_demo",
    #                    api_secrets_file="api_secret.json",
    #                    settings_file="settings.json")
    stock = StockBybit()
    db_filepath = "main.db"
    if r == "1":
        data_collector.collect_stream_tickers(
            stock=stock,
            filepath=db_filepath,
            pair="BTCUSDT",
            recreate=True)

    elif r == "2":
        data_collector.collect_history_candles(
            stock=stock,
            filepath=db_filepath,
            recreate=True,
            pair="BTCUSDT",
            interval="5",
            start='14.09.2024 13:00:00,00')
    elif r == "3":
        data_show.draw_candles(db_filepath, pair="BTCUSDT")


if __name__ == "__main__":
    main()

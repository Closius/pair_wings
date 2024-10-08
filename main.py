import os
import json5
import logging
import threading

from lib import data_show, data_collector, utils

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
    log.info("6 - Trade demo: open SHORT")
    log.info("7 - Trade demo: close whole SHORT")
    log.info("8 - Quit")
    r = input()
    log.info(r)
    map = MapBybit()
    stock = StockBybit(map=map, account_name="pair_wings_demo",
                       api_secrets_file="bybit_api_secret.json",
                       settings_file="bybit_settings.json")
    # stock = StockBybit(map=map)
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
    elif r == "6":
        ticker = stock.get_ticker(pair="BTCUSDT")
        log.info(f"MarkPrice: {ticker.MarkPrice}")
        precision = utils.get_precision(ticker.MarkPrice)
        p1 = round(utils.percentage(percent=1, whole=ticker.MarkPrice), precision)
        stopLoss = round(ticker.MarkPrice + p1/2, precision)
        takeProfit = round(ticker.MarkPrice - 3*p1, precision)
        log.info(f" + 1%: {p1}")
        log.info(f"stopLoss: {stopLoss}")
        log.info(f"takeProfit: {takeProfit}")
        amount = 0.01 * ticker.MarkPrice
        log.info(f"amount: {amount}")
        stock.open_modify_SHORT_LONG(side="SHORT", pair="BTCUSDT",
                         amount_money_add=amount, stopLoss=stopLoss,
                         takeProfit=takeProfit)

        stock.open_modify_SHORT_LONG(side="SHORT", pair="BTCUSDT",
                         amount_money_add=amount)

    elif r == "7":
        position = stock.get_position_status(pair="BTCUSDT", verbose=True)
        if position:
            log.info(f"estimated profit: {position.Profit_}")
            stock.close_SHORT_LONG(pair="BTCUSDT", amount_percent=100)



if __name__ == "__main__":
    main()

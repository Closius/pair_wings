import os
import time

import json5
import random
import statistics
import logging
import threading
import numpy as np

from lib import data_show, data_collector, utils

from lib.stocks.stock_bybit import StockBybit
from lib.stocks.db_map.map_bybit import MapBybit


def open_add_position(stock, side, percent_from_deposit=1.0, qty=0.01, wait_for_add_second=None, add_qty=0.01):
    log = logging.getLogger(__name__)
    ticker = stock.get_ticker(pair="BTCUSDT")
    log.info(f"Opening {side}:")
    log.info(f"\tpercent_from_deposit: {percent_from_deposit}")
    log.info(f"\tqty: {qty}")
    log.info(f"\twait_for_add_second: {wait_for_add_second}")
    log.info(f"\tadd_qty: {add_qty}")
    log.info(f"\t---")
    log.info(f"\tMarkPrice: {ticker.MarkPrice}")
    precision = stock.get_instrument_info(pair="BTCUSDT").PriceScale
    position_side = utils.position_side(side)
    p1 = round(utils.percentage(percent=percent_from_deposit, whole=ticker.MarkPrice), precision)
    stopLoss = round(ticker.MarkPrice - (p1 / 2) * position_side, precision)
    takeProfit = round(ticker.MarkPrice + (3 * p1) * position_side, precision)
    log.info(f"\t + 1%: {p1}")
    amount = qty * ticker.MarkPrice
    stock.open_modify_SHORT_LONG(side=side, pair="BTCUSDT",
                                 amount_money_add=amount, stopLoss=stopLoss,
                                 takeProfit=takeProfit)

    if wait_for_add_second:
        time.sleep(wait_for_add_second)
        amount = add_qty * ticker.MarkPrice
        stock.open_modify_SHORT_LONG(side=side, pair="BTCUSDT",
                                     amount_money_add=amount)

def close_position(stock, amount_percent=100):
    log = logging.getLogger(__name__)
    balance_init = stock.get_USDT_deposit()
    position = stock.get_position_status(pair="BTCUSDT", verbose=True)
    if position:
        stock.close_SHORT_LONG(pair="BTCUSDT", amount_percent=amount_percent)
    balance_end = stock.get_USDT_deposit()
    earn_net = balance_end - balance_init
    log.info(f"Earned netto (the fact from stock): {earn_net}")
    error_percent = round(utils.error_percent(experiment=earn_net,
                                      theory=position.Closed_PL_Money), 2)
    log.info(f"Error calculated PL and earned: {error_percent} %")

    return earn_net, error_percent, position.ROI_percent, position.Unrealized_PL_Money


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
    log.info("8 - Trade demo: get position status")
    log.info("9 - Trade demo: statistical error")
    log.info("10 - Quit")
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
        open_add_position(stock, side="SHORT", percent_from_deposit=1, qty=0.01,
                    wait_for_add_second=None, add_qty=0.01)

    elif r == "7":
        earn_net, error_percent, ROI_percent, unrealized_PnL = close_position(stock, amount_percent=100)
        log.info(f"earn_net: {earn_net}")
        log.info(f"error_percent: {error_percent}")
        log.info(f"ROI_percent: {ROI_percent}")
        log.info(f"unrealized_PnL: {unrealized_PnL}")
    elif r == "8":
        position = stock.get_position_status(pair="BTCUSDT", verbose=True)
    elif r == "9":
        earn_nets = []
        error_percents = []
        ROI_percents = []
        unrealized_PnLs = []
        nos = 100
        for i in range(nos):
            log.info(f"")
            log.info(f"")
            log.info(f" ================>  STEP {i+1} of {nos}")
            log.info(f"")
            log.info(f"")
            wait_for_add_second = random.randint(-3, 30)
            if wait_for_add_second <= 0:
                wait_for_add_second = None
            open_add_position(stock, side=random.choice(["SHORT", "LONG"]),
                              percent_from_deposit=random.uniform(0.5, 3.0),
                              qty=0.01,
                              wait_for_add_second=wait_for_add_second,
                              add_qty=0.01)
            wait_for_close_seconds = random.randint(10, 30)
            log.info(f"wait_for_close_seconds: {wait_for_close_seconds}")
            time.sleep(wait_for_close_seconds)
            earn_net, error_percent, ROI_percent, unrealized_PnL = close_position(stock, amount_percent=100)
            earn_nets.append(earn_net)
            error_percents.append(error_percent)
            ROI_percents.append(ROI_percent)
            unrealized_PnLs.append(unrealized_PnL)
        log.info("====== Summary ======")
        log.info(f"error_percents: theory > experiment = negative")
        log.info(f"")
        log.info(f"earn_nets = {earn_nets}")
        log.info(f"error_percents = {error_percents}")
        log.info(f"ROI_percents = {ROI_percents}")
        log.info(f"unrealized_PnLs = {unrealized_PnLs}")
        log.info(f"---")
        log.info(f"earn_nets MAX: {max(earn_nets)}")
        log.info(f"earn_nets MIN: {min(earn_nets)}")
        log.info(f"earn_nets MEAN: {statistics.mean(earn_nets)}")
        log.info(f"---")
        log.info(f"The BEST earn prediction: {max(error_percents)}")
        log.info(f"The WORST earn prediction: {min(error_percents)}")
        log.info(f"The AVERAGE earn prediction: {statistics.mean(error_percents)}")
        log.info(f"---")
        log.info(f"ROI_percents MAX: {max(ROI_percents)}")
        log.info(f"ROI_percents MIN: {min(ROI_percents)}")
        log.info(f"ROI_percents MEAN: {statistics.mean(ROI_percents)}")
        log.info(f"---")
        log.info(f"unrealized_PnLs MAX: {max(unrealized_PnLs)}")
        log.info(f"unrealized_PnLs MIN: {min(unrealized_PnLs)}")
        log.info(f"unrealized_PnLs MEAN: {statistics.mean(unrealized_PnLs)}")
        log.info(f"---")
        e_upl = np.corrcoef(earn_nets, unrealized_PnLs)[0][1]
        e_ROI = np.corrcoef(earn_nets, ROI_percents)[0][1]
        e_err = np.corrcoef(earn_nets, error_percents)[0][1]
        log.info(f"Correlation earn_nets vs unrealized_PnLs: {e_upl}")
        log.info(f"Correlation earn_nets vs ROI_percents: {e_ROI}")
        log.info(f"Correlation earn_nets vs error_percents: {e_err}")
        log.info(f"---")
        log.info(f"If any correlation is higher than 0.95 - you can use it as a metric!")

        import matplotlib.pyplot as plt
        plt.style.use('ggplot')

        fig, ax = plt.subplots()
        ax.plot(earn_nets, unrealized_PnLs, linewidth=0, marker='s', label='unrealized_PnL', color='green')
        ax.plot(earn_nets, ROI_percents, linewidth=0, marker='s', label='ROI_percent', color='red')
        ax.set_xlabel('earn_nets')
        ax.set_ylabel('unrealised_PnL/ROI_percent')
        ax.legend(facecolor='white')
        plt.show()


if __name__ == "__main__":
    main()

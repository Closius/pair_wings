import json
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


def open_add_position(stock, pair, side, percent_from_deposit=1.0, qty=0.01, wait_for_add_second=None, add_qty=0.01):
    log = logging.getLogger(__name__)
    ticker = stock.get_ticker(pair=pair)
    log.info(f"Opening {side}:")
    log.info(f"\tpair {pair}:")
    log.info(f"\tpercent_from_deposit: {percent_from_deposit}")
    log.info(f"\tqty: {qty}")
    log.info(f"\twait_for_add_second: {wait_for_add_second}")
    log.info(f"\tadd_qty: {add_qty}")
    log.info(f"\t---")
    log.info(f"\tMarkPrice: {ticker.MarkPrice}")
    precision = stock.get_instrument_info(pair=pair).PriceScale
    position_side = utils.position_side(side)
    p1 = round(utils.percentage(percent=percent_from_deposit, whole=ticker.MarkPrice), precision)
    stopLoss = round(ticker.MarkPrice - (p1 / 2) * position_side, precision)
    takeProfit = round(ticker.MarkPrice + (3 * p1) * position_side, precision)
    log.info(f"\t + 1%: {p1}")
    amount = qty * ticker.MarkPrice
    stock.open_modify_SHORT_LONG(side=side, pair=pair,
                                 amount_money_add=amount, stopLoss=stopLoss,
                                 takeProfit=takeProfit)

    if wait_for_add_second:
        log.info(f"wait_for_add_second: {wait_for_add_second}")
        time.sleep(wait_for_add_second)
        amount = add_qty * ticker.MarkPrice
        stock.open_modify_SHORT_LONG(side=side, pair=pair,
                                     amount_money_add=amount)

def close_position(stock, pair, amount_percent=100, verbose=False):
    log = logging.getLogger(__name__)
    balance_init = stock.get_USDT_deposit()
    position = stock.get_position_status(pair=pair, verbose=verbose)
    if position:
        stock.close_SHORT_LONG(pair=pair, amount_percent=amount_percent)
    balance_end = stock.get_USDT_deposit()
    earn_net = balance_end - balance_init
    log.info(f"Earned netto (the fact from stock): {earn_net}")
    error_percent = round(utils.error_percent(experiment=earn_net,
                                      theory=position.Closed_PL_Money), 2)
    log.info(f"Error calculated PL and earned: {error_percent} %")

    return {"earn_net": earn_net,
         "error_percent": error_percent,
         "ROI_percent": position.ROI_percent,
         "Unrealized_PL_Money": position.Unrealized_PL_Money,
         "Closed_PL_Money": position.Closed_PL_Money}


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

    pair = "WIFUSDT"
    # pair = "BTCUSDT"

    log.info("==========================")
    log.info("Choose your destiny:")
    log.info("1 - Collect streams: candle, ticker, order book")
    log.info("2 - Collect candles")
    log.info("3 - Show candles")
    log.info("4 - Read order books")
    log.info("5 - Read stream candles")
    log.info("6 - Trade demo: open SHORT wait close")
    log.info("7 - Trade demo: get position status")
    log.info("8 - Trade demo: statistical error")
    log.info("9 - Quit")
    log.info("")
    log.info(f"pair: {pair}")
    log.info("")
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
        dc.collect_stream_tickers(pair=pair, stop_event=event, recreate=True)
        dc.collect_stream_candles_ticker(pair=pair, interval="5", stop_event=event, recreate=True)
        dc.collect_stream_order_book(pair=pair, stop_event=event, recreate=True)

        log.info("==========================")
        log.info("Press Enter to Stop collection")
        input()
        event.set()
        log.info("Interrupted")

    elif r == "2":
        dc = data_collector.DataCollector(stock, db_filepath, map)
        dc.collect_history_candles(pair=pair, interval="5",
                                   start='16.09.2024 19:00:00,00',
                                   end=None,
                                   recreate=True)

    elif r == "3":
        data_show.draw_candles(db_filepath, pair=pair, map=map)
    elif r == "4":
        data_show.read_order_book(db_filepath, pair=pair, map=map)
    elif r == "5":
        data_show.read_stream_candles(db_filepath, pair=pair, interval="5", map=map)
    elif r == "6":
        open_add_position(stock, pair=pair, side="SHORT", percent_from_deposit=1, qty=0.01,
                    wait_for_add_second=None, add_qty=0.01)

        # time.sleep(20)
        # r = close_position(stock, pair=pair, amount_percent=100, verbose=True)
    elif r == "7":
        position = stock.get_position_status(pair=pair, verbose=True)
    elif r == "8":
        results = {}
        nos = 100
        min_qty = stock.get_min_order_qty_price(pair=pair, verbose=True)["qty"]
        precision_qty = stock.get_instrument_info(pair=pair).QtyScale
        qty = min_qty + round(utils.percentage(percent=100, whole=min_qty), precision_qty)
        for i in range(nos):
            log.info(f"")
            log.info(f"")
            log.info(f" ================>  STEP {i+1} of {nos}")
            log.info(f"")
            log.info(f"")
            try:
                wait_for_add_second = random.randint(-3, 30)
                if wait_for_add_second <= 0:
                    wait_for_add_second = None
                open_add_position(stock, pair=pair, side=random.choice(["SHORT", "LONG"]),
                                  percent_from_deposit=1, #random.uniform(0.5, 3.0),
                                  qty=qty,
                                  wait_for_add_second=wait_for_add_second,
                                  add_qty=qty)
                wait_for_close_seconds = random.randint(10, 30)
                log.info(f"wait_for_close_seconds: {wait_for_close_seconds}")
                time.sleep(wait_for_close_seconds)
                r = close_position(stock, pair=pair, amount_percent=100, verbose=True)
                if i == 0:
                    results = {x: [] for x in r.keys()}
            except Exception as ex:
                log.exception(ex)
                continue
            else:
                for k, v in r.items():
                    results[k].append(v)
        log.info(f"")
        log.info(f"")
        log.info("====== Summary ======")
        log.info(f"")
        log.info(f"error_percent: theory > experiment = negative")
        log.info(f"")
        log.info(json.dumps(results, indent=4))
        log.info(f"")
        for k, v in results.items():
            log.info(f"---")
            log.info(f"{k} MAX: {max(v)}")
            log.info(f"{k} MIN: {min(v)}")
            log.info(f"{k} MEAN: {statistics.mean(v)}")
        log.info(f"---")
        exclude = ["error_percent"]
        for k, v in results.items():
            if (k != "earn_net") and (k not in exclude):
                corr = np.corrcoef(results["earn_net"], v)[0][1]
                log.info(f"Correlation earn_nets vs {k}: {corr}")
        log.info(f"If any correlation is higher than 0.95 - you can use it as a metric!")

        import matplotlib as mpl
        import matplotlib.pyplot as plt
        plt.style.use('ggplot')
        fig, ax = plt.subplots()
        # https://matplotlib.org/stable/gallery/color/colormap_reference.html
        # ax.set_prop_cycle(color=mpl.colormaps["Set1"].colors)
        colors = mpl.colormaps["Set1"].colors
        mn = []
        mx = []
        i = 0
        for k, v in results.items():
            color = colors[i]
            if k not in exclude:
                ax.plot(results["earn_net"], v, linewidth=0, marker='s', label=k, color=color)
                ax.plot(results["earn_net"], np.poly1d(np.polyfit(results["earn_net"], v, 1))(results["earn_net"]), color=color)
                mn.append(min(v))
                mx.append(max(v))
            if i == len(colors) - 1:
                i = 0
            else:
                i += 1
        mn = min(mn)
        mx = max(mx)
        ax.set_xlim([mn, mx])
        ax.set_ylim([mn, mx])
        ax.set_title(f"pair: {pair}, points: {len(results['earn_net'])}")

        ax.set_xlabel('earn_net')
        ax.set_ylabel('value')
        ax.legend(facecolor='white')
        plt.show()

if __name__ == "__main__":
    main()

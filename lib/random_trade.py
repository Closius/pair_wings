import json
import os
import time
import queue
import random
import statistics
import logging
from concurrent.futures import ThreadPoolExecutor

import matplotlib as mpl
import matplotlib.pyplot as plt

plt.style.use('ggplot')

import numpy as np

from lib import utils


def open_add_position(stock, pair, side, percent_from_deposit=1.0, qty=0.01, wait_for_add_second=None, add_qty=0.01):
    log = logging.getLogger(pair)
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
    log = logging.getLogger(pair)
    position = stock.get_position_status(pair=pair, verbose=verbose)
    if position:
        earn_net = stock.close_SHORT_LONG(pair=pair, amount_percent=amount_percent)
    else:
        raise ValueError("Position not exist. Maybe closed?")
    error_percent = round(utils.error_percent(experiment=earn_net,
                                      theory=position.Closed_PL_Money), 2)
    log.info(f"Error calculated PL and Earned netto: {error_percent} %")

    return {"earn_net": earn_net,
         "error_percent": error_percent,
         "ROI_percent": position.ROI_percent,
         "Unrealized_PL_Money": position.Unrealized_PL_Money,
         "Closed_PL_Money": position.Closed_PL_Money}

def random_trade(pair, stock, n_steps, folder):
    if not os.path.exists(folder):
        os.mkdir(folder)
    log = utils.setup_logger(pair, os.path.join(folder, f"{pair}.log"), level=logging.INFO, stream=True)
    results = {}
    exclude = ["error_percent"]
    min_qty = stock.get_min_order_qty_price(pair=pair, verbose=True)["qty"]
    precision_qty = stock.get_instrument_info(pair=pair).QtyScale
    qty = min_qty + round(utils.percentage(percent=100, whole=min_qty), precision_qty)
    for i in range(n_steps):
        log.info(f"")
        log.info(f"")
        log.info(f" ================>  {pair} STEP {i + 1} of {n_steps}")
        log.info(f"")
        log.info(f"")
        try:
            # wait_for_add_second = random.randint(-3, 30)
            # if wait_for_add_second <= 0:
            #     wait_for_add_second = None
            wait_for_add_second = None
            open_add_position(stock, pair=pair, side=random.choice(["SHORT", "LONG"]),
                              percent_from_deposit=1,  # random.uniform(0.5, 3.0),
                              qty=qty,
                              wait_for_add_second=wait_for_add_second,
                              add_qty=qty)
            wait_for_close_seconds = random.randint(10, 30)
            log.info(f"wait_for_close_seconds: {wait_for_close_seconds}")
            time.sleep(wait_for_close_seconds)
            r = close_position(stock, pair=pair, amount_percent=100, verbose=True)
        except Exception as ex:
            log.exception(ex)
            continue
        else:
            if not results:
                results = {x: [] for x in r.keys()}
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
    for k, v in results.items():
        if (k != "earn_net") and (k not in exclude):
            corr = np.corrcoef(results["earn_net"], v)[0][1]
            log.info(f"Correlation earn_nets vs {k}: {corr}")
    log.info(f"If any correlation is higher than 0.95 - you can use it as a metric!")

    return results

def random_trade_plot_results(results, pair, folder=None, save_only=True):
    exclude = ["error_percent"]

    if not results:
        return
    fig, ax = plt.subplots()
    # https://matplotlib.org/stable/gallery/color/colormap_reference.html
    # ax.set_prop_cycle(color=mpl.colormaps["Set1"].colors)
    colors = mpl.colormaps["Set1"].colors
    mn = []
    mx = []
    i = 0
    lns = []
    new_axis = ["ROI_percent"]
    for k, v in results.items():
        if k in new_axis:
            _ax = ax.twinx()
            _ax.set_ylabel(k)
            # _ax.set_yscale('log')
            _ax.set_xlim([min(v), max(v)])
            _ax.set_ylim([min(v), max(v)])
            _ax.grid(visible=False)
        else:
            _ax = ax

        color = colors[i]
        if k not in exclude:
            _ax.scatter(results["earn_net"], v, marker='s', color=color, s=3)
            lns += _ax.plot(results["earn_net"],
                            np.poly1d(np.polyfit(results["earn_net"], v, 1))(results["earn_net"]),
                            color=color, label=k, linewidth=1)
            if k not in new_axis:
                mn.append(min(v))
                mx.append(max(v))
        for step, (x, y) in enumerate(zip(results["earn_net"], v)):
            _ax.annotate(str(step + 1), (x, y), fontsize=5, color=color)

        if i == len(colors) - 1:
            i = 0
        else:
            i += 1

    ax.grid(visible=True, linestyle='--')
    mn = min(mn)
    mx = max(mx)
    ax.set_xlim([mn, mx])
    ax.set_ylim([mn, mx])
    ax.set_title(f"pair: {pair}, points: {len(results['earn_net'])}")

    ax.set_xlabel('earn_net')
    ax.set_ylabel('value')
    labs = [l.get_label() for l in lns]
    ax.legend(lns, labs, fontsize=5)

    if save_only:
        fig.savefig(os.path.join(folder, f"{pair}_{len(results['earn_net'])}.png"), dpi=300)  # save the figure to file
        plt.close(fig)  # close the figure window
    else:
        plt.show()


def main(pairs, stock, num_steps):
    log = logging.getLogger()
    def one_pair(pair, stock, n_steps, folder):
        results = random_trade(pair=pair, stock=stock, n_steps=n_steps, folder=folder)
        random_trade_plot_results(results, pair=pair, folder=folder, save_only=True)

    total_pairs = len(pairs)

    log.info(f"")
    log.info(f"")
    log.info(f"                   RANDOM TRADE")
    log.info(f"")
    log.info(f"")
    log.info(f"pairs for test {total_pairs}: {pairs}")
    log.info(f"num_steps: {num_steps}")
    log.info(f"")

    def callback(future):
        log.info(f"finished: {future.pair__}")

    with ThreadPoolExecutor(max_workers=None) as executor:
        i = 1
        while pairs:
            pair = pairs.pop(0)
            future = executor.submit(
                one_pair,
                pair=pair,
                stock=stock,
                n_steps=num_steps,
                folder="results"
            )
            future.pair__ = pair
            future.add_done_callback(callback)
            log.info(f"launch {i} of {total_pairs}: {pair}")
            i += 1

import logging

import matplotlib.pyplot as plt
import mplfinance as mpf

import pandas as pd

import database


def draw_candles(db_filepath, pair):
    log = logging.getLogger(__name__)
    db = database.DB(db_filepath)
    data_candle = db.read_candle_table(pair)

    # apd = mpf.make_addplot(data_candle['High'], type='scatter')
    # fig, axlist = mpf.plot(data_candle, type='candle', style='charles', title=pair,
    #                        addplot=apd, volume=True, returnfig=True)

    fig, axlist = mpf.plot(data_candle, type='candle', style='charles', title=pair,
                           volume=True, returnfig=True)

    mpf.show()

def draw_tickers_and_candles(db_filepath, pair):
    """
        Do not use. For reference only
    """
    log = logging.getLogger(__name__)
    db = database.DB(db_filepath)
    data_ticker = db.read_ticker_table(pair)
    data_candle = db.read_candle_table(pair)

    # data_ticker.reset_index(drop=True, inplace=True)
    # data_candle.reset_index(drop=True, inplace=True)
    # data = data_candle.merge(data_ticker, how="outer", on="Time")
    # data.index = pd.DatetimeIndex(data['Time'])
    # data_candle.index = pd.DatetimeIndex(data_candle['Time'])

    fig, (ax_candles, ax_volumes) = plt.subplots(2, 1, layout=None)

    ax = ax_candles.twiny()
    t = pd.date_range(
        start=data_candle.index.min(),
        end=data_candle.index.max(),
        freq="1ms"
    )
    data = t.to_frame().merge(data_ticker, how="outer", left_index=True, right_index=True)
    ax.plot(data.index, data["markPrice"])

    # show everything on one plot
    mpf.plot(data, ax=ax_candles,
             type="candle", volume=ax_volumes
    )

    mpf.show()
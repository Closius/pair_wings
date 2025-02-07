import logging

import matplotlib.pyplot as plt
import mplfinance as mpf
import seaborn as sns

import pandas as pd

from lib.backend import database, utils


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

def read_order_book(db_filepath, pair):
    log = logging.getLogger(__name__)
    db = database.DB(db_filepath)
    data_order_book = db.read_order_book_table(pair)

    log.info(f"data_order_book: {data_order_book.info(verbose=True)}")

    fig, ax = plt.subplots()
    ax.set_xlabel("Price")
    ax.set_ylabel("Quantity")

    for index, row in data_order_book.iterrows():

        ax.set_title(f"Order Book. {utils.datetime_to_text(row['Time'])}")

        ask_price = []
        ask_qty = []
        for a, a1 in row['Asks'].tolist():
            ask_price.append(a)
            ask_qty.append(a1)
        bid_price = []
        bid_qty = []
        for a, a1 in row['Bids'].tolist():
            bid_price.append(a)
            bid_qty.append(a1)

        ask_df = pd.DataFrame({'price': ask_price, 'quantity': ask_qty})
        bid_df = pd.DataFrame({'price': bid_price, 'quantity': bid_qty})

        # log.info(f"ask_df: {ask_df}")
        # log.info(f"bid_df: {bid_df}")
        # log.info("====================================================")

        sns.ecdfplot(x="price", weights="quantity", stat="count",
                     data=ask_df, ax=ax, color="red")
        sns.ecdfplot(x="price", weights="quantity", stat="count",
                        complementary=True, data=bid_df, ax=ax, color="green")
        # complementary=True allows reflects that lower bids are "better"

        plt.pause(0.5)
        ax.clear()

def read_stream_candles(db_filepath, pair, interval):
    log = logging.getLogger(__name__)
    db = database.DB(db_filepath)
    df = db.read_candle_ticker_table(pair, interval)

    log.info(df.info(verbose=True))
    # log.info(df)


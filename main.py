import logging
import threading
import time

from lib import data_show, data_collector, utils, random_trade

from lib.stocks.stock_bybit import StockBybit


def main():
    log = utils.setup_logger("", "pybit.log", level=logging.INFO, stream=True)

    # pair = "WIFUSDT"
    pair = "BTCUSDT"

    log.info("==========================")
    log.info("Choose your destiny:")
    log.info("1 - Collect streams: candle, ticker, order book")
    log.info("2 - Collect candles")
    log.info("3 - Show candles")
    log.info("4 - Read order books")
    log.info("5 - Read stream candles")
    log.info("6 - Trade demo: stream_position_status, open SHORT wait close")
    log.info("7 - Trade demo: statistical error")
    log.info("8 - Test dataframe")
    log.info("9 - Quit")
    log.info("")
    log.info(f"pair: {pair}")
    log.info("")
    r = input()
    log.info(r)
    stock = StockBybit(account_name="pair_wings_demo",
                       api_secrets_file="bybit_api_secret.json",
                       settings_file="bybit_settings.json")
    # stock = StockBybit(map=map)
    db_filepath = "main.db"
    event = threading.Event()
    if r == "1":
        dc = data_collector.DataCollector(stock, db_filepath)
        dc.collect_stream_tickers(pair=pair, stop_event=event, recreate=True)
        dc.collect_stream_candles_ticker(pair=pair, interval="5", stop_event=event, recreate=True)
        dc.collect_stream_order_book(pair=pair, stop_event=event, recreate=True)

        log.info("==========================")
        log.info("Press Enter to Stop collection")
        input()
        event.set()
        log.info("Interrupted")

    elif r == "2":
        dc = data_collector.DataCollector(stock, db_filepath)
        dc.collect_history_candles(pair=pair, interval="5",
                                   start_utc='06.12.2024 19:00:00,00',
                                   end_utc=None,
                                   recreate=True)

    elif r == "3":
        data_show.draw_candles(db_filepath, pair=pair)
    elif r == "4":
        data_show.read_order_book(db_filepath, pair=pair)
    elif r == "5":
        data_show.read_stream_candles(db_filepath, pair=pair, interval="5")
    elif r == "6":

        def handler(message):
            for m in message:
                log.info(f'position_status {utils.datetime_to_text(m.UpdatedTime)} | '
                              f'{m.Pair} | {m.Size}' )

        stock.stream_position_status(handler=handler, handler_kwargs={}, stop_event=event)
        time.sleep(2)
        random_trade.open_add_position(stock, pair=pair, side="SHORT", percent_from_deposit=1, qty=0.01,
                    wait_for_add_second=3, add_qty=0.01)
        time.sleep(5)
        r = random_trade.close_position(stock, pair=pair, amount_percent=100, verbose=True)
        event.set()

    elif r == "7":
        pairs = ['ACEUSDT', 'BTCUSDT', 'COREUSDT', 'DASHUSDT', 'EOSUSDT', 'ETHUSDT', 'HMSTRUSDT',
            'MNTUSDT', 'SOLUSDT', 'MONUSDT'] #, 'WIFUSDT', 'RAREUSDT']
        pairs = stock.get_all_pairs()

        # pairs = ['BTCUSDT']

        pairs_USDT_only = [pair for pair in pairs if pair.endswith("USDT")]
        pairs_USDT_only = pairs_USDT_only[:10]  # first N
        random_trade.main(pairs=pairs_USDT_only, stock=stock, num_steps=10)
    elif r == "8":
        from lib.state_collection import State
        tk1 = stock.get_ticker(pair)
        tk1.FundingRate = None
        time.sleep(2)
        tk2 = stock.get_ticker(pair)

        st = State(ticker=tk1)
        # st = State()
        st.append_single_snapshot(ticker=tk2)
        st.append_single_snapshot(ticker=tk2)

        log.info("ticker:")
        st._dataframes['ticker'].info()
        log.info("position:")
        st._dataframes['position'].info()
        log.info("order_book:")
        st._dataframes['order_book'].info()

        for k in st._dataframes.keys():
            st._dataframes[k] = st._dataframes[k].drop(index=[0])

        log.info("order_book:")
        st._dataframes['order_book'].info()

if __name__ == "__main__":
    main()

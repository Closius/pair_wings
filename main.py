import logging
import threading

from lib import data_show, data_collector, utils, random_trade

from lib.stocks.stock_bybit import StockBybit
from lib.stocks.db_map.map_bybit import MapBybit


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
    log.info("6 - Trade demo: open SHORT wait close")
    log.info("7 - Trade demo: get position status")
    log.info("8 - Trade demo: statistical error")
    log.info("9 - Get all pairs")
    log.info("10 - Quit")
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
        random_trade.open_add_position(stock, pair=pair, side="SHORT", percent_from_deposit=1, qty=0.01,
                    wait_for_add_second=None, add_qty=0.01)

        # time.sleep(20)
        # r = random_trade.close_position(stock, pair=pair, amount_percent=100, verbose=True)
    elif r == "7":
        position = stock.get_position_status(pair=pair, verbose=True)
    elif r == "8":
        # 10 because of connections limit
        # pairs = ['ACEUSDT', 'BTCUSDT', 'COREUSDT', 'DASHUSDT', 'EOSUSDT', 'ETHUSDT', 'HMSTRUSDT',
        #     'MNTUSDT', 'SOLUSDT', 'MONUSDT'] #, 'WIFUSDT', 'RAREUSDT']

        pairs = stock.get_all_pairs()

        pairs_USDT_only = [pair for pair in pairs if pair.endswith("USDT")]

        number_of_pairs_in_simultaneous_trade = 10
        random_trade.main(pairs=pairs_USDT_only, stock=stock, num_steps=100,
                          number_of_pairs_in_simultaneous_trade=number_of_pairs_in_simultaneous_trade)

    elif r == "9":
        pairs = stock.get_all_pairs()
        log.info(pairs)

if __name__ == "__main__":
    main()

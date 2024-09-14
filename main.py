import os
import json5
import logging
import threading
import concurrent.futures

from pybit.unified_trading import HTTP

import data_collector
import data_show

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

    account_name = "pair_wings_demo"
    with open("api_secret.json") as f:
        api_secrets = json5.load(f)
    with open("settings.json") as f:
        settings = json5.load(f)

    log.info("Current settings:")
    log.info(json5.dumps(settings, indent=4))

    log.info(f"Connecting to: '{account_name} ...'")
    # You can create an authenticated or unauthenticated HTTP session.
    # You can skip authentication by not passing any value for the key and secret.
    session = HTTP(
        api_key=api_secrets["accounts"][account_name]["API_KEY"],
        api_secret=api_secrets["accounts"][account_name]["API_SECRET"],
        demo=True,
    )

    log.info("==========================")
    log.info("Current settings:")
    log.info("1 - Collect tickers")
    log.info("2 - Collect candles")
    log.info("3 - Show data")
    log.info("4 - Quit")
    r = int(input())
    log.info(r)
    db_filepath = "main.db"
    if r == 1:
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            event = threading.Event()
            future = executor.submit(
                data_collector.collect_tickers,
                filepath=db_filepath,
                pair="BTCUSDT",
                recreate=True,
                stop_event=event,
            )
            log.info("==========================")
            log.info("Press any key to Stop collection")
            r = input()
            log.info(r)
            event.set()
            log.info("Interrupted")
            try:
                future.result()
            except Exception as exc:
                log.exception(exc)

    elif r == 2:
        data_collector.collect_history_candles(
            filepath=db_filepath,
            recreate=True,
            pair="BTCUSDT",
            interval=30,
            start='13.09.2024 13:00:00,00')
    elif r == 3:
        data_show.draw_candles(db_filepath, pair="BTCUSDT")
    elif r == 4:
        pass

if __name__ == "__main__":
    main()

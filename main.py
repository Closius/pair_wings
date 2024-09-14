import os
import json5
import logging
import threading
import concurrent.futures

from pybit.unified_trading import HTTP

import data_collector


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
    log.info("1 - Collect data")
    log.info("2 - Run main")
    r = int(input())
    log.info(r)
    if r == 1:
        db_filepath = "BTCUSDT.db"
        if os.path.exists(db_filepath):
            log.info(f"File exist {db_filepath} remove Y ?")
            if input() == "Y":
                os.remove(db_filepath)
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            event = threading.Event()
            future_to_url = executor.submit(
                data_collector.collect_tickers,
                session=session,
                filepath=db_filepath,
                pair="BTCUSDT",
                stop_event=event,
            )
            log.info("==========================")
            log.info("Press any key to Stop collection")
            r = input()
            log.info(r)
            event.set()
            log.info("Interrupted")
    elif r == 2:
        # wb = session.get_wallet_balance(accountType="UNIFIED")
        # log.info("Wallet balance:")
        # log.info(json5.dumps(wb, indent=4))

        # order_SHORT = Order(session, order_id=f"deal_{1}__SHORT", settings=settings)
        # order_SHORT.create_market(
        #     side="SHORT", symbol="BTCUSDT", value=100, stopLoss=57400.0, takeProfit=57000.0
        # )

        log.info(
            json5.dumps(
                session.get_order_history(
                    category="linear",
                    limit=1,
                ),
                indent=4,
            )
        )

        # for symbol in settings["accounts"][account_name]["pairs"]:
        #     session.set_leverage(
        #         category="inverse",
        #         symbol=symbol,
        #         buyLeverage=str(settings["accounts"][account_name]),
        #         sellLeverage=str(settings["accounts"][account_name]),
        #     )
        #
        # log.info("Wallet balance:")
        # log.info(json5.dumps(wb, indent=4))
        #
        # ob = session.get_orderbook(category="linear", symbol="BTCUSDT")
        # log.info("Order book BTCUSDT:")
        # log.info(json5.dumps(ob, indent=4))
        #
        # tickers = session.get_tickers(category="linear", symbol="BTCUSDT")
        # log.info("get_tickers BTCUSDT:")
        # log.info(json5.dumps(tickers, indent=4))


if __name__ == "__main__":
    main()

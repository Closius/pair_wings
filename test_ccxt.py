# -*- coding: utf-8 -*-

import asyncio
import os
import sys

import pandas as pd

from sqlalchemy import create_engine

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# import ccxt.async_support as ccxt  # noqa: E402
import ccxt.pro as ccxtpro


async def main(symbol):
    db_path = os.path.join(os.path.expanduser("~"), "pair_wings_CCXT.db")
    print(f"db: {db_path}")
    engine = create_engine(f"sqlite:///{db_path}", echo=True)
    exchange = ccxtpro.bybit()
    # while True:
    #     print("--------------------------------------------------------------")
    #     # print(exchange.iso8601(exchange.milliseconds()), "fetching", symbol, "ticker from", exchange.name)
    #     # this can be any call really
    #     from_datetime = "2025-02-12 00:00:00"
    #     from_timestamp = exchange.parse8601(from_datetime)
    #
    #     ticker = await exchange.fetch_ohlcv(symbol, "5m", from_timestamp)
    #
    #     print(ticker)

    print("--------------------------------------------------------------")
    # print(exchange.iso8601(exchange.milliseconds()), "fetching", symbol, "ticker from", exchange.name)
    # this can be any call really
    from_datetime = "2025-02-12 00:00:00"
    from_timestamp = exchange.parse8601(from_datetime)

    ohlcv = await exchange.fetch_ohlcv(symbol, "5m", from_timestamp)

    df = pd.DataFrame(ohlcv, columns=["TIME", "OPEN", "HIGH", "LOW", "CLOSE", "VOLUME"])
    df["TIME"] = pd.to_datetime(df["TIME"], unit="ms")

    df.info()

    df.to_sql(name="ohlcv", con=engine, if_exists="replace", index=False)

    dff = pd.read_sql("ohlcv", engine)

    dff.info()

    print(df == dff)

    await exchange.close()


asyncio.run(main("BTC/USDT"))

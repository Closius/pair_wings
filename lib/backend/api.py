import os
import logging
from typing import List, Dict

import pandas as pd
import json5

from lib.misc import utils

from lib.backend.stocks.stock_bybit import StockBybit
from lib.backend.data_collector import DataCollector


class BackendApi:

    def __init__(self):
        self.log = utils.setup_logger(
            "", os.path.join(os.path.expanduser("~"), "pair_wings.log"), level=logging.DEBUG, stream=True
        )
        self.stock_name = None
        self.account_name = None
        self.stock: StockBybit | None = None
        self.db_filepath = os.path.join(os.path.expanduser("~"), "pair_wings.db")
        self.data_collector: DataCollector | None = None

    def read_api_secrets(self, api_secrets_file: str) -> Dict:
        with open(api_secrets_file) as f:
            return json5.load(f)

    @property
    def is_stock_connected(self):
        if not self.stock:
            return False
        return self.stock.is_alive

    def connect_stock(self, stock_name: str, account_name: str, api_key: str, api_secret: str):
        self.stock_name = stock_name
        self.account_name = account_name
        self.stock = StockBybit(account_name=account_name, api_key=api_key, api_secret=api_secret)
        self.data_collector = DataCollector(stock=self.stock, filepath=self.db_filepath)

    def disconnect_stock(self):
        if self.stock:
            self.stock.disconnect()
            self.stock = None
        if self.data_collector:
            self.data_collector = None
        self.stock_name = None
        self.account_name = None

    def get_all_pairs(self) -> List[str]:
        pairs = self.stock.get_all_pairs()
        pairs_USDT_only = [pair for pair in pairs if pair.endswith("USDT")]
        return pairs_USDT_only

    def get_available_intervals(self) -> List[str]:
        return list(self.stock.get_available_intervals().keys())

    def collect_candles(self, pair, interval, start_utc, end_utc=None):
        self.data_collector.collect_history_candles(
            pair=pair, interval=interval, start_utc=start_utc, end_utc=end_utc, recreate=True
        )

    def get_candles(self, pair, interval) -> pd.DataFrame:
        return self.data_collector.db.read_candle_table(pair, interval)

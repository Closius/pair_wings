import logging
from typing import List, Dict

import json5

from lib.backend import data_collector, data_show, random_trade, utils

from lib.backend.stocks.stock_bybit import StockBybit


class BackendApi:

    def __init__(self):
        self.log = utils.setup_logger("", "../../pybit.log", level=logging.DEBUG, stream=True)
        self.stock_name = None
        self.account_name = None
        self.is_connected = False
        self.stock: StockBybit | None = None
        self.db_filepath = "../../main.db"

    def read_api_secrets(self, api_secrets_file: str) -> Dict:
        with open(api_secrets_file) as f:
            return json5.load(f)

    def connect_stock(self, stock_name: str, account_name: str, api_key: str, api_secret: str):
        if self.is_connected:
            ValueError(f"Stock: {self.stock_name}, account: {self.account_name} - already connected. Disconnect first")

        self.stock_name = stock_name
        self.account_name = account_name
        self.stock = StockBybit(account_name=account_name, api_key=api_key, api_secret=api_secret)
        self.is_connected = True

    def disconnect_stock(self):
        if self.is_connected:
            self.stock.disconnect()

    def get_all_pairs(self, stock_name: str, account_name: str) -> List[str]:
        pairs = self.stock[stock_name][account_name].get_all_pairs()
        pairs_USDT_only = [pair for pair in pairs if pair.endswith("USDT")]
        return pairs

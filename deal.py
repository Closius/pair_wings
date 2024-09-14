import os
import json5
import logging
import time
import order


class Deal:

    def __init__(self, session, deal_id: int, settings: dict):
        self.deal_id = deal_id
        self.settings = settings
        self.session = session
        self.order_SHORT = None
        self.order_LONG = None
        self.log = logging.getLogger(__name__)

    def _get_current_USDT_deposit(self):
        wb = self.session.get_wallet_balance(accountType="UNIFIED")
        for coin in wb["result"]["list"][0]["coin"]:
            if coin["coin"] == "USDT":
                return coin["walletBalance"]

    # def create_deal(self):
    #
    #     amount_USDT = (amount_USDT__percent / 100) * self._get_current_USDT_deposit()
    #     self.order_SHORT = order.Order(
    #         self.session, order_id=f"deal_{self.deal_id}__SHORT", settings=self.settings
    #     )
    #
    #     self.order_LONG = order.Order(
    #         self.session, order_id=f"deal_{self.deal_id}__LONG", settings=self.settings
    #     )

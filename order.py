import os
import json5
import logging


class Order:

    def __init__(self, session, order_id: str, settings: dict):
        self.order_id = order_id
        self.settings = settings
        self.session = session
        self.log = logging.getLogger(__name__)

    def _value_to_qty(self, value, symbol):
        """
        https://bybit-exchange.github.io/docs/v5/market/tickers
        """
        tickers = self.session.get_tickers(category="linear", symbol=symbol)
        mp = tickers["result"]["list"][0]["markPrice"]
        qty = value / float(mp)
        self.log.info(f"value_to_qty {symbol} price {mp}: {value} -> {qty}")
        if symbol == "BTCUSDT":
            qty = round(qty, 3)
        return qty

    def create_market(self, side, symbol, value, stopLoss, takeProfit):
        """

        https://bybit-exchange.github.io/docs/v5/order/create-order

        symbol: BTCUSDT
        :param side: SHORT, LONG
        :return:
        """
        if side == "LONG":
            side = "Buy"
            positionIdx = 1
        elif side == "SHORT":
            side = "Sell"
            positionIdx = 2
        positionIdx = 0
        # Place an order on that USDT Perpetual
        self.log.info(
            self.session.place_order(
                category="linear",
                orderLinkId=self.order_id,
                symbol=symbol,
                isLeverage=1,
                side=side,
                orderType="Market",
                qty=self._value_to_qty(value, symbol),
                # Used to identify positions in different position modes. Under hedge-mode, this param is required
                # 0: one-way mode
                # 1: hedge-mode Buy side
                # 2: hedge-mode Sell side
                positionIdx=positionIdx,
                takeProfit=takeProfit,
                stopLoss=stopLoss,
                # https://www.bybit.com/en/help-center/article/What-Are-Time-In-Force-TIF-GTC-IOC-FOK
                timeInForce="IOC",
                tpTriggerBy="LastPrice",
                slTriggerBy="LastPrice",
                tpslMode="Full",
            )
        )

    def create_limit(self, side, symbol, price, stopLoss, takeProfit):
        """

        https://bybit-exchange.github.io/docs/v5/order/create-order

        symbol: BTCUSDT
        :param side: SHORT, LONG
        :return:
        """
        if side == "LONG":
            side = "Buy"
            positionIdx = 1
        elif side == "SHORT":
            side = "Sell"
            positionIdx = 2
        # Place an order on that USDT Perpetual
        self.log.info(
            self.session.place_order(
                category="linear",
                orderLinkId=self.order_id,
                symbol=symbol,
                isLeverage=1,
                side=side,
                orderType="Limit",
                price=price,
                # Used to identify positions in different position modes. Under hedge-mode, this param is required
                # 0: one-way mode
                # 1: hedge-mode Buy side
                # 2: hedge-mode Sell side
                positionIdx=positionIdx,
                takeProfit=takeProfit,
                stopLoss=stopLoss,
                # https://www.bybit.com/en/help-center/article/What-Are-Time-In-Force-TIF-GTC-IOC-FOK
                timeInForce="IOC",
                tpTriggerBy="LastPrice",
                slTriggerBy="LastPrice",
                tpslMode="Full",
            )
        )

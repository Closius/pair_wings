import logging
import time

import json5
import numpy as np

from pybit.unified_trading import WebSocket
from pybit.unified_trading import HTTP

from lib.stocks.stock_interface import IStock, atomic_in_threads
from lib import utils

from lib.stocks.db_map.map_interface import (IMap, ITicker, ICandle, ICandleTicker, IOrderBook, IPosition,
                                             IInstrumentInfo)

from lib.stocks.db_map.map_bybit import PositionBybit


class StockBybit(IStock):
    """
        Note: Rate limit is implemented inside `pybit`
            https://bybit-exchange.github.io/docs/v5/rate-limit
    """

    CROSS_MARGIN = True

    def __init__(self, map: IMap, account_name=None, api_secrets_file=None, settings_file=None, demo=True):
        super().__init__(map=map)
        self.log_stock = logging.getLogger()
        self.log_stock.info(f"Connecting to public Bybit ...")
        self.demo = demo
        self.http = HTTP(demo=True)
        self.http_private = None
        self.ws = WebSocket(
            testnet=True,  # testnet gives wrong values! at least on HTTP
            channel_type="linear"
        )

        if account_name:
            self.log_stock.info(f"Connecting to private Bybit: {account_name} ...")

            with open(api_secrets_file) as f:
                api_secrets = json5.load(f)
            with open(settings_file) as f:
                settings = json5.load(f)

            # self.log_stock.info("Current settings:")
            # self.log_stock.info(json5.dumps(settings, indent=4))

            # You can create an authenticated or unauthenticated HTTP session.
            # You can skip authentication by not passing any value for the key and secret.
            self.http_private = HTTP(
                api_key=api_secrets["accounts"][account_name]["API_KEY"],
                api_secret=api_secrets["accounts"][account_name]["API_SECRET"],
                demo=demo,
                recv_window=20000
            )

            self.ws_private = WebSocket(
                demo=demo,
                testnet=False,
                channel_type="private",
                api_key=api_secrets["accounts"][account_name]["API_KEY"],
                api_secret=api_secrets["accounts"][account_name]["API_SECRET"],
            )

    def _amount_money_to_qty(self, amount_money, pair):
        """
        https://bybit-exchange.github.io/docs/v5/market/tickers
        """
        log = logging.getLogger(pair)
        tickers = self.http_private.get_tickers(category="linear", symbol=pair)
        mp = float(tickers["result"]["list"][0]["markPrice"])
        qty = amount_money / mp
        log.info(f"value_to_qty {pair} price {mp}: {amount_money} -> {qty}")
        precision_qty = self.get_instrument_info(pair=pair, verbose=False).QtyScale
        qty = round(qty, precision_qty)
        return qty

    def get_min_order_qty_price(self, pair, verbose=False):
        log = logging.getLogger(pair)
        if verbose:
            log.info(f"Minimum order limits {pair}:")
        inst_info = self.get_instrument_info(pair=pair, verbose=False)
        tickers = self.http_private.get_tickers(category="linear", symbol=pair)
        mp = float(tickers["result"]["list"][0]["markPrice"])
        if inst_info.MinOrderQty * mp < inst_info.MinOrderValue:
            min_in_money = inst_info.MinOrderValue
        else:
            min_in_money = inst_info.MinOrderQty * mp
        min_in_qty = min_in_money / mp
        r = {"qty": round(min_in_qty, inst_info.QtyScale), "money": round(min_in_money, inst_info.PriceScale)}
        if verbose:
            log.info(f"\tmarkPrice current: {mp}")
            log.info(f"\tqty: {r['qty']}")
            log.info(f"\tqty in money: {r['money']}")

        return r

    def get_USDT_deposit(self):
        wb = self.http_private.get_wallet_balance(accountType="UNIFIED")
        for coin in wb["result"]["list"][0]["coin"]:
            if coin["coin"] == "USDT":
                return float(coin["walletBalance"])

    def get_funding_rate(self, pair, verbose=False):
        ticker_obj = self.get_ticker(pair=pair)
        return ticker_obj.FundingRate

    def get_instrument_info(self, pair, verbose=False):
        log = logging.getLogger(pair)
        if verbose:
            log.info(f"Instrument info {pair}:")
        if pair not in self._instrument_infos:
            instr_info = self.http.get_instruments_info(
                category="linear",
                symbol=pair,
            )

            r = IInstrumentInfo()
            r.MaxLeverage = float(instr_info["result"]["list"][0]["leverageFilter"]["maxLeverage"])
            r.PriceScale = int(instr_info["result"]["list"][0]["priceScale"])
            min_qty_raw_str = instr_info["result"]["list"][0]["lotSizeFilter"]["minOrderQty"]
            r.MinOrderQty = float(min_qty_raw_str)
            if "." in min_qty_raw_str:
                r.QtyScale = len(min_qty_raw_str.split(".")[1])
            else:
                r.QtyScale = 0
            r.OrderQtyStep = float(instr_info["result"]["list"][0]["lotSizeFilter"]["qtyStep"])
            r.MinOrderValue = float(instr_info["result"]["list"][0]["lotSizeFilter"]["minNotionalValue"])

            # Makers initiate orders, adding liquidity to the market,
            # while takers execute these orders, consuming liquidity
            if self.demo is False:
                fee_rates = self.http_private.get_fee_rates(
                    category="linear",
                    symbol=pair,
                )
                r.TakerFeeRate = float(fee_rates["result"]["list"][0]["takerFeeRate"])
                r.MakerFeeRate = float(fee_rates["result"]["list"][0]["makerFeeRate"])
            else:
                r.TakerFeeRate = 0.0550 / 100
                r.MakerFeeRate = 0.0200 / 100

            self._instrument_infos[pair] = r

            # if verbose:
            #     log.info("\t" + json.dumps(instr_info, indent=4))

        if verbose:
            log.info(f"\tMaxLeverage: {self._instrument_infos[pair].MaxLeverage}")
            log.info(f"\tPriceScale: {self._instrument_infos[pair].PriceScale}")
            log.info(f"\tQtyScale: {self._instrument_infos[pair].QtyScale}")
            log.info(f"\tTakerFeeRate: {self._instrument_infos[pair].TakerFeeRate}")
            log.info(f"\tMakerFeeRate: {self._instrument_infos[pair].MakerFeeRate}")
            log.info(f"\tMinOrderQty: {self._instrument_infos[pair].MinOrderQty}")
            log.info(f"\tOrderQtyStep: {self._instrument_infos[pair].OrderQtyStep}")
            log.info(f"\tMinOrderValue: {self._instrument_infos[pair].MinOrderValue}")

        return self._instrument_infos[pair]

    @atomic_in_threads(IStock.GET_FACT_EARN_NET_rwlock, "OBEY")
    def open_modify_SHORT_LONG(self, side, pair, amount_money_add=None, stopLoss=None, takeProfit=None):
        log = logging.getLogger(pair)
        if amount_money_add and amount_money_add <= 0:
            raise ValueError("amount_money must be > 0. HINT: To close the position use "
                             "close_SHORT_LONG() or open the opposite position")
        pos_info = self.get_position_status(pair=pair)
        qty = self._amount_money_to_qty(amount_money_add, pair)
        # log.info(json5.dumps(pos_info, indent=4))
        if pos_info is None:
            msg = f"Opening {side} position: ~{amount_money_add} money (qty: {qty}) on {pair}, stopLoss={stopLoss}, takeProfit={takeProfit}"
        else:
            w_msg = []
            if amount_money_add:
                w_msg.append(f"add {amount_money_add} money")
            if stopLoss:
                if stopLoss != pos_info.StopLoss:
                    w_msg.append(f"stopLoss={stopLoss}")
            if takeProfit:
                if takeProfit != pos_info.TakeProfit:
                    w_msg.append(f"takeProfit={takeProfit}")
            if len(w_msg) == 0:
                raise ValueError("Nothing to do")
            msg = f"Modifying to {side} position (~{pos_info.Size * pos_info.MarkPrice_} money (qty: {qty})) on {pair}: " + ", ".join(w_msg)

        log.info(msg)

        if side == "LONG":
            side = "Buy"
        elif side == "SHORT":
            side = "Sell"

        kwrgs = {
            "category": "linear",
            "symbol": pair,
            # "isLeverage": 1,  # spot only
            "side": side,
            "orderType": "Market",
            "marketUnit": "baseCoin",  # baseCoin - qty in BTC, quoteCoin - qty in USDT
            "qty": qty,
            # Used to identify positions in different position modes. Under hedge-mode, this param is required
            # 0: one-way mode
            # 1: hedge-mode Buy side
            # 2: hedge-mode Sell side
            "positionIdx": 0,
            # https://www.bybit.com/en/help-center/article/What-Are-Time-In-Force-TIF-GTC-IOC-FOK
            "timeInForce": "IOC",
            "tpTriggerBy": "LastPrice",
            "slTriggerBy": "LastPrice",
            "tpslMode": "Full"
        }
        if stopLoss:
            kwrgs["stopLoss"] = stopLoss
        if takeProfit:
            kwrgs["takeProfit"] = takeProfit

        # Place an order on that USDT Perpetual
        orderId = self.http_private.place_order(**kwrgs)['result']['orderId']

        log.info(f"<< Completed >>. {msg}")

        return orderId

    @atomic_in_threads(IStock.GET_FACT_EARN_NET_rwlock, "ATOMIC")
    def close_SHORT_LONG(self, pair, amount_percent=100):
        """
        Close by market price

        if amount_percent=100 - all the qty (coins) will be closed

        :param uid:
        :return:
        """
        log = logging.getLogger(pair)
        msg = f"Closing position: {amount_percent} % on {pair}"
        log.info(msg)
        if (amount_percent > 100) or (amount_percent <= 0):
            raise ValueError(f"amount_percent should be 100>x>=0")
        pos_info = self.get_position_status(pair=pair)
        if pos_info is None:
            raise ValueError("current position is zero, nothing to close")
        original_position_size = pos_info.Size
        size_coins_to_close = original_position_size * (amount_percent / 100)
        side = pos_info.Side
        size_to_close = "Sell" if side == "LONG" else "Buy"

        balance_init = self.get_USDT_deposit()

        # https://stackoverflow.com/questions/71056977/how-can-i-closing-my-position-with-using-market-order-via-bybit-api
        orderId = self.http_private.place_order(
            category="linear",
            symbol=pair,
            side=size_to_close,
            orderType="Market",
            qty=size_coins_to_close,
            # https://www.bybit.com/en/help-center/article/What-Are-Time-In-Force-TIF-GTC-IOC-FOK
            timeInForce="GTC",
            reduceOnly=True,
            closeOnTrigger=False
        )['result']['orderId']

        current_order_size = None
        while (original_position_size - size_coins_to_close) != current_order_size:
            pos_info = self.get_position_status(pair=pair)
            if pos_info is None:
                break
            time.sleep(0.5)
            current_order_size = pos_info.Size

        balance_end = self.get_USDT_deposit()
        earn_net = balance_end - balance_init
        log.info(f"Earned netto (the fact from stock): {earn_net}")
        log.info(f"<< Completed >>. {msg}")
        return earn_net

    def formula_AEP(self, entry_qty_price_list: list):
        """
        Calculate Average entry price

        https://www.bybit.com/en/help-center/article/Profit-Loss-calculations-USDT-ContractUSDT_Perpetual_UTA

            Average entry price = Total contract value in USDT/Total quantity of contracts
            Total contract value in USDT = ( (Quantity1 x Price1) + (Quantity2 x Price2)...)
            By using the figures above:

            Total contract value in USDT
            = ( (Quantity1 x Price1) + (Quantity2 x Price2) )
            = ( (0.5 x 5,000) + (0.3 x 6,000) )
            = 4300
            Total quantity of contracts
            = 0.5 + 0.3
            = 0.8 BTC
            Average Entry Price
             = 4,300 / 0.8
            = 5,375

        :return:
        """
        total_contract_value_in_usdt = 0
        total_quantity_contracts = 0
        for q, p in entry_qty_price_list:
            total_contract_value_in_usdt += q * p
            total_quantity_contracts += q
        return total_contract_value_in_usdt / total_quantity_contracts

    def formula_profit_loss(self, pair, side, average_entry_price_usdt, last_traded_price, qty,
                            margin_leverage_pair, margin_leverage_pair_max, funding_rate, verbose=False):
        """
        Calculate the profit/losses (what you get in wallet) from the closing order by market

        https://www.bybit.com/en/help-center/article/Profit-Loss-calculations-USDT-ContractUSDT_Perpetual_UTA

        :return:
        """


        """
            https://medium.com/derivadex/liquidation-and-bankruptcy-prices-under-the-hood-c93167950d6a
        """
        log = logging.getLogger(pair)
        if verbose:
            log.info(f"[formula] common input:")
            log.info(f"[formula] \taverage_entry_price_usdt: {average_entry_price_usdt}")
            log.info(f"[formula] \tlast_traded_price: {last_traded_price}")
            log.info(f"[formula] \tqty: {qty}")
            log.info(f"[formula] \tmargin_leverage_pair: {margin_leverage_pair}")
            log.info(f"[formula] \tmargin_leverage_pair_max: {margin_leverage_pair_max}")
            log.info(f"[formula] \tfunding_rate: {funding_rate}")
            log.info(f"[formula] \tposition_side: {side}")

        if verbose:
            log.info(f"[formula] calculating 'unrealized_pl_usdt':")
        entry_price_usdt = average_entry_price_usdt
        position_side = utils.position_side(side)
        unrealized_pl_usdt = qty * position_side * (last_traded_price - entry_price_usdt)
        if verbose:
            log.info(f"[formula] \tunrealized_pl_usdt: {unrealized_pl_usdt}")

        """
            https://medium.com/derivadex/liquidation-and-bankruptcy-prices-under-the-hood-c93167950d6a
                
            https://www.bybit.com/en/help-center/article/Bankruptcy-Price-USDT-Contract
            
            For Buy/Long:
            Bankruptcy Price= Entry Price × (1 - Initial Margin Rate*)
            
            For Sell/Short:
            Bankruptcy Price= Entry Price × (1 + Initial Margin Rate*)
            *Initial Margin Rate (IMR) = 1/ Leverage
            
        """

        if verbose:
            log.info(f"[formula] calculating 'bankruptcy_price':")
        collateral = (qty * entry_price_usdt) / margin_leverage_pair  # init margin
        # total_account_value = collateral + unrealized_pl_usdt
        # bankruptcy_price_common_calc = last_traded_price - position_side * (total_account_value / qty)
        # bankruptcy_price_common_calc gives the same result as below
        bankruptcy_price = entry_price_usdt * (1 - position_side * (1 / margin_leverage_pair))
        bankruptcy_price_max_lev = entry_price_usdt * (1 - position_side * (1 / margin_leverage_pair_max))

        if verbose:
            log.info(f"[formula] \tcollateral (init margin): {collateral}")
            log.info(f"[formula] \tcollateral (init margin) based on max leverage: {(qty * entry_price_usdt) / margin_leverage_pair_max}")
            # log.info(f"[formula] \ttotal_account_value: {total_account_value}")
            # log.info(f"[formula] \tbankruptcy_price_common_calc: {bankruptcy_price_common_calc}")
            log.info(f"[formula] \tbankruptcy_price: {bankruptcy_price}")
            log.info(f"[formula] \tbankruptcy_price based on max leverage: {bankruptcy_price_max_lev}")

        """
            https://www.bybit.com/en/help-center/article/Profit-Loss-calculations-USDT-ContractUSDT_Perpetual_UTA
        
            Unrealized P&L%
    
            Unrealized P&L% basically shows the Return on Investment (ROI) of the position 
            in its percentage form. Similar to Unrealized P&L, the figure shows changes 
            depending on the movement of the Last Traded Price. As such, the Unrealized 
            PNL% or ROI formula is below.
            
            Unrealized P&L% = [ Position's unrealized P&L / Position Margin ] x 100%
            Position Margin = Initial margin + Fee to close
            
            Using Trader B as an example, Trader B holds an existing BTCUSDT open buy position 
            of 0.2 qty with an entry price of USD 7,000. When the Last Traded Price inside 
            the order book is showing USD 7,500, the unrealized P&L shown will be 100 USDT. 
            Assuming the leverage used is 10x. 
                     
            Based on our earlier calculation, the position's unrealized P&L = 100 USDT
            Initial margin = (Qty x Entry price) / leverage = (0.2 x 7000) /10 = 140 USDT
            Fee to close = Bankruptcy price x Qty x 0.055% = 6,300 x 0.2 x 0.055% = 0.693 USDT
            Unrealized P&L% = [ 100 USDT / ( 140 USDT + 0.693 USDT ) ] x 100% = 71.07%
            
            For cross margin mode, the position margin will always be calculated using 
            the maximum leverage allowed under the current risk limit level for the 
            particular coin (Example BTCUSDT = 100x). 
            
            Under Cross margin mode:
            
            Unrealized P&L% = Unrealized P&L /(initial margin + fee to close) X 100%
            
        """
        """
            Why ROI is important? 
            
            P&L is short for Profit and Losses. It is the statement that indicates how much you earned, 
            how much it cost you to make that earning, and what the net result is (i.e. a profit or a loss). 
            A very widely used index is the profit/loss as a percentage of your main income source 
            (eg sales of goods, revenue on services rendered, etc.). That way you make companies 
            with different sizes, currencies, etc. comparable. The P&L, however, does not indicate 
            how much investment you had to make to generate such results.
    
            This is where the ROI comes in. With the P&L bottom line number (the net gain from your 
            operations in a given timeframe), you can can compare how much return you had on your assets 
            invested. E.g. just saying that you had a $1 million profit doesn't tell how good your 
            investment is. You need to know how much money you allocated to the business/investment 
            to create the profit. If you need $1billion invested in your business to generate 
            $1 million, I'd rather buy 100 million in US government bonds and haver a much higher ROI.
            
            Profit and loss is just how much money you made (or lost). It is stated in absolute terms, 
            not as a percentage of your investment. ROI is stated in terms of your investment 
            and your timeline.

            Earning $1,000 would be great if your initial investment was $10 and you made the money in 
            a year. Earning $1,000 would be terrible if your initial investment was $1MM and you 
            made the money over five years.
        """

        if verbose:
            log.info(f"[formula] calculating 'ROI_or_unrealized_pl_percent':")

        # TODO: investigate if it should be used the max margin for collateral calculation
        if self.CROSS_MARGIN:
            margin_leverage = margin_leverage_pair_max
        # collateral = (qty * entry_price_usdt) / margin_leverage_pair  # init margin
        # TODO: why bankruptcy_price ?  But it returns value that mach with the stock UI
        fee_to_close = bankruptcy_price * qty * self.get_instrument_info(pair).TakerFeeRate
        # fee_to_close = last_traded_price * qty * self.get_instrument_info(pair).TakerFeeRate
        position_margin = collateral + fee_to_close

        ROI_or_unrealized_pl_percent = (unrealized_pl_usdt / position_margin) * 100

        if verbose:
            log.info(f"[formula] \tfee_to_close (based on bankruptcy_price): {fee_to_close}")
            log.info(f"[formula] \tposition_margin: {position_margin}")
            log.info(f"[formula] \tROI_or_unrealized_pl_percent: {ROI_or_unrealized_pl_percent}")

        """
            Closed P&L   
            
            When traders finally close their position, the P&L becomes realized and is recorded 
            inside the Closed P&L tab within the Assets page. Unlike unrealized P&L, there are 
            some major differences in the calculation. Below summarizes the differences between 
            the unrealized P&L and closed P&L. 
            
            Therefore, assuming full closing of the entire position, the formula for calculating 
            Closed P&L is as follows:
            
            Closed P&L = Position P&L - Fee to open - Fee to close - Sum of all funding fees paid/received
            
            Using Trader C as an example, Trader C holds an existing BTCUSDT open sell position of 
            0.4 qty with an entry price of USD 6,000. When the Last Traded Price inside the order 
            book is showing USD 5,000, trader C decided to close the entire position via the Close 
            by Market function. 
            
             
            
            Assuming that Trader C also opened the position via a market order and funding fees 
            totaling 2.10 USDT were paid out while holding the position. 
            
            Fee to open = Qty x Entry price x 0.055% = 1.32 USDT paid out
            Fee to close = Qty x Exit price x 0.055% = 1.1 USDT paid out
            Sum of all funding fees paid/received = 2.10 USDT paid out
            Closed P&L = 400 - 1.32 - 1.1 - 2.10 = 395.48 USDT
             
            
            Note: 
            a) The above example only applies when the entire position is opened and closed via a 
            single order in both directions. 
            b) For partial closing of positions, Closed P&L will prorate all fees (fee to open 
            and funding fee(s)) according to the percentage of the position partially closed and 
            use the pro-rated figure to compute the Closed P&L
            c) Traders can view their Closed P&L history from here. 
            
        """
        if verbose:
            log.info(f"[formula] calculating 'closed_pl_usdt':")
        fee_to_open = qty * entry_price_usdt * self.get_instrument_info(pair).TakerFeeRate
        exit_price_usdt = last_traded_price
        fee_to_close = qty * exit_price_usdt * self.get_instrument_info(pair).TakerFeeRate

        # TODO: should be calculated if taken
        # fee_funding = qty * last_traded_price * funding_rate
        fee_funding = 0

        closed_pl_usdt = unrealized_pl_usdt - fee_to_open - fee_to_close - fee_funding

        if verbose:
            log.info(f"[formula] \tfee_funding: {fee_funding}")
            log.info(f"[formula] \tfee_to_open: {fee_to_open}")
            log.info(f"[formula] \tfee_to_close: {fee_to_close}")
            log.info(f"[formula] \tclosed_pl_usdt: {closed_pl_usdt}")

        return {"Unrealized_PL_Money": unrealized_pl_usdt,
                "ROI_percent": ROI_or_unrealized_pl_percent,
                "Closed_PL_Money": closed_pl_usdt}

    def get_history_tohlcv(self, pair, interval, start, end=None):
        kargs = {
            "category": "linear",
            "symbol": pair,
            "interval": interval,
            "start": utils.datetime_text_to_ts(start),
        }
        if end:
            kargs["end"] = utils.datetime_text_to_ts(end)

        # TODO: it doesnt return everything! probably pagination
        # It is not efficient but allow to use an universal DataCollector
        for candle in self.http.get_kline(**kargs)["result"]["list"]:
            response = ICandle()
            for (k,v), data in zip(self.map.candle.init_fields.items(), candle):
                if v.db_name == self.map.candle.Time.db_name:
                    setattr(response, k, utils.ts_to_datetime(data))
                else:
                    setattr(response, k, data)

            yield response

    def get_ticker(self, pair):
        message = self.http_private.get_tickers(category="linear",
                                                symbol=pair)

        response = ITicker()
        response.Time = utils.ts_to_datetime(message["time"])
        message = message["result"]["list"][0]
        for k, v in self.map.ticker.init_fields.items():
            if v.db_name == self.map.ticker.Time.db_name:
                continue
            else:
                setattr(response, k, float(message[v.api_name]))
        return response

    def get_all_pairs(self):
        message = self.http_private.get_tickers(category="linear")
        pairs = []
        for m in message["result"]["list"]:
            pairs.append(m["symbol"])

        return pairs

    def get_position_status(self, pair, verbose=False):
        log = logging.getLogger(pair)
        pos_info = self.http_private.get_positions(
            category="linear",
            symbol=pair,
        )
        if (len(pos_info["result"]["list"]) == 0) or (pos_info["result"]["list"][0]["size"] == "0"):
            if verbose:
                log.info("No position opened")
            return None
        data = pos_info["result"]["list"][0]
        if verbose:
            log.info(f"Position on {pair}:")
            log.info(f"initial margin (from stock): {data['positionIM']}")
            log.info(f"Bankruptcy price (from stock): {data['bustPrice']}")
            # log.info(json.dumps(data, indent=4))

        map_position = PositionBybit(request_type="http")
        response = IPosition()
        response.Pair = pair
        response.CreatedTime = utils.ts_to_datetime(data[map_position.CreatedTime.api_name])
        response.UpdatedTime = utils.ts_to_datetime(data[map_position.UpdatedTime.api_name])
        response.Side = "SHORT" if data[map_position.Side.api_name] == "Sell" else "LONG"
        response.Size = float(data[map_position.Size.api_name])
        response.AvgPrice = float(data[map_position.AvgPrice.api_name]) # self.formula_AEP(entry_qty_price_list=)
        response.Leverage = float(data[map_position.Leverage.api_name])
        response.MarkPrice_ = float(data[map_position.MarkPrice_.api_name])
        response.StopLoss = None if data[map_position.StopLoss.api_name] == "" else float(data[map_position.StopLoss.api_name])
        response.TakeProfit = None if data[map_position.TakeProfit.api_name] == "" else float(data[map_position.TakeProfit.api_name])

        instrument_info_obj = self.get_instrument_info(pair=pair)

        pl_dict = self.formula_profit_loss(pair=pair,
                                           side=response.Side,
                                           average_entry_price_usdt=response.AvgPrice,
                                           last_traded_price=response.MarkPrice_,
                                           qty=response.Size,
                                           margin_leverage_pair=response.Leverage,
                                           margin_leverage_pair_max=instrument_info_obj.MaxLeverage,
                                           funding_rate=self.get_funding_rate(pair=pair),
                                           verbose=verbose)

        response.Unrealized_PL_Money = pl_dict["Unrealized_PL_Money"]
        response.ROI_percent = pl_dict["ROI_percent"]
        response.Closed_PL_Money = pl_dict["Closed_PL_Money"]

        if verbose:
            # log.info("ProfitLoss (calculated):")
            log.info(f"\tUnrealized_PL_Money: {response.Unrealized_PL_Money}")
            log.info(f"\tROI_percent: {response.ROI_percent}")
            log.info(f"\tClosed_PL_Money: {response.Closed_PL_Money}")

            log.info("ProfitLoss (from stock):")
            log.info(f"\tUnrealised PnL: {data['unrealisedPnl']}")
            log.info(f"\tThe realised PnL for the current holding position: {data['curRealisedPnl']}")
            # log.info(f"\tAll time cumulative realised P&L: {data['cumRealisedPnl']}")

        return response

    @IStock.stream_decorator
    def stream_tohlcv(self, handler, handler_kwargs, stop_event, pair, interval):
        """
        https://bybit-exchange.github.io/docs/v5/websocket/public/kline
        """

        log = logging.getLogger(pair)

        def handle_kline(message):
            # reformat
            try:
                data = message["data"][0]
                response = ICandleTicker()
                for k, v in self.map.candle_ticker.init_fields.items():
                    if v.db_name in [self.map.candle_ticker.Time.db_name,
                                     self.map.candle_ticker.Start.db_name,
                                     self.map.candle_ticker.End.db_name]:
                        setattr(response, k, utils.ts_to_datetime(data[v.api_name]))
                    else:
                        setattr(response, k, data[v.api_name])

                handler(response, **handler_kwargs)
            except Exception as ex:
                log.exception(ex)
                self.log_stock.error(f"Happened on {pair}")
                self.log_stock.exception(ex)

        self.ws.kline_stream(interval, pair, handle_kline)

        while not stop_event.is_set():
            pass

    @IStock.stream_decorator
    def stream_ticker(self, handler, handler_kwargs, stop_event, pair):
        log = logging.getLogger(pair)
        def handle_ticker(message):
            # reformat
            try:
                message["data"].update({"ts": message["ts"]})
                response = ITicker()
                for k, v in self.map.ticker.init_fields.items():
                    if v.db_name == self.map.ticker.Time.db_name:
                        setattr(response, k, utils.ts_to_datetime(message["data"][v.api_name]))
                    else:
                        setattr(response, k, message["data"][v.api_name])

                handler(response, **handler_kwargs)
            except Exception as ex:
                log.exception(ex)
                self.log_stock.error(f"Happened on {pair}")
                self.log_stock.exception(ex)

        self.ws.ticker_stream(pair, handle_ticker)

        while not stop_event.is_set():
            pass

    @IStock.stream_decorator
    def stream_order_book(self, handler, handler_kwargs, stop_event, pair):
        """
            https://bybit-exchange.github.io/docs/v5/websocket/public/orderbook
        """

        log = logging.getLogger(pair)

        def handle_ticker(message):
            handle_ticker.asks_d_snapshot = None
            handle_ticker.bids_d_snapshot = None

            def asks_bids_delta_snapshot(raw_data, is_snapshot, big_snapshot: dict | None) -> dict | None:
                df = {float(p): float(v) for p, v in raw_data}
                if is_snapshot:
                    return df
                else:
                    if isinstance(big_snapshot, dict):
                        res = {}
                        for p, v in big_snapshot.items():
                            if p not in df:
                                continue
                            elif df[p] == 0:
                                continue
                            else:
                                res[p] = df[p]
                        return res
                    else:
                        return None

            # reformat
            try:
                is_snapshot = True if message["type"] == "snapshot" else False

                response = IOrderBook()

                response.Time = utils.ts_to_datetime(message["ts"])

                handle_ticker.asks_d_snapshot = asks_bids_delta_snapshot(raw_data=message["data"][self.map.order_book.Asks.api_name],
                                                                         is_snapshot=is_snapshot,
                                                                         big_snapshot=handle_ticker.asks_d_snapshot)
                if handle_ticker.asks_d_snapshot is None:
                    return
                else:
                    response.Asks = np.array([[p,v] for p,v in handle_ticker.asks_d_snapshot.items()])

                handle_ticker.bids_d_snapshot = asks_bids_delta_snapshot(raw_data=message["data"][self.map.order_book.Bids.api_name],
                                                                         is_snapshot=is_snapshot,
                                                                         big_snapshot=handle_ticker.bids_d_snapshot)
                if handle_ticker.bids_d_snapshot is None:
                    return
                else:
                    response.Bids = np.array([[p,v] for p,v in handle_ticker.bids_d_snapshot.items()])

                handler(response, **handler_kwargs)
            except Exception as ex:
                log.exception(ex)
                self.log_stock.error(f"Happened on {pair}")
                self.log_stock.exception(ex)

        self.ws.orderbook_stream(depth=50, symbol=pair, callback=handle_ticker)

        while not stop_event.is_set():
            pass

    @IStock.stream_decorator
    def stream_position_status(self, handler, handler_kwargs, stop_event):
        def handle_position(message):
            # reformat
            try:
                responses = []
                for data in message["data"]:
                    map_position = PositionBybit(request_type="websocket")
                    response = IPosition()
                    response.Pair = data[map_position.Pair.api_name]
                    response.CreatedTime = utils.ts_to_datetime(data[map_position.CreatedTime.api_name])
                    response.UpdatedTime = utils.ts_to_datetime(data[map_position.UpdatedTime.api_name])
                    response.Side = "SHORT" if data[map_position.Side.api_name] == "Sell" else "LONG"
                    response.Size = float(data[map_position.Size.api_name])
                    response.AvgPrice = float(
                        data[map_position.AvgPrice.api_name])  # self.formula_AEP(entry_qty_price_list=)
                    response.Leverage = float(data[map_position.Leverage.api_name])
                    response.MarkPrice_ = float(data[map_position.MarkPrice_.api_name])
                    response.StopLoss = None if data[map_position.StopLoss.api_name] == "" else float(
                        data[map_position.StopLoss.api_name])
                    response.TakeProfit = None if data[map_position.TakeProfit.api_name] == "" else float(
                        data[map_position.TakeProfit.api_name])

                    instrument_info_obj = self.get_instrument_info(pair=response.Pair)

                    if data["size"] != "0":

                        pl_dict = self.formula_profit_loss(pair=response.Pair,
                                                           side=response.Side,
                                                           average_entry_price_usdt=response.AvgPrice,
                                                           last_traded_price=response.MarkPrice_,
                                                           qty=response.Size,
                                                           margin_leverage_pair=response.Leverage,
                                                           margin_leverage_pair_max=instrument_info_obj.MaxLeverage,
                                                           funding_rate=self.get_funding_rate(pair=response.Pair),
                                                           verbose=False)

                        response.Unrealized_PL_Money = pl_dict["Unrealized_PL_Money"]
                        response.ROI_percent = pl_dict["ROI_percent"]
                        response.Closed_PL_Money = pl_dict["Closed_PL_Money"]
                    else:
                        response.Unrealized_PL_Money = None
                        response.ROI_percent = None
                        response.Closed_PL_Money = None

                    responses.append(response)

                handler(responses, **handler_kwargs)
            except Exception as ex:
                self.log_stock.exception(ex)

        self.ws_private.position_stream(handle_position)

        while not stop_event.is_set():
            pass

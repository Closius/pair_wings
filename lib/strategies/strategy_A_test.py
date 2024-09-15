from lib.strategies.strategy_intefrace import IStrategy


class Strategy_A_Test(IStrategy):

    def __init__(self, stock_model, uid, pair, history_tohlcv):
        super(IStrategy).__init__(stock_model, uid, pair, history_tohlcv)

    def update_instruments(self):
        pass

    def update_trade_info(self):
        pass

    def make_decision(self):
        pass

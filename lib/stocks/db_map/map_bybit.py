from lib.stocks.db_map.map_interface import ITicker, ICandle, ICandleTicker, IOrderBook, IMap


class TickerBybit(ITicker):
    def __init__(self):
        super().__init__()
        self.Time.api_name = "ts"
        self.MarkPrice.api_name = "markPrice"
        self.Ask1Size.api_name = "ask1Size"
        self.Bid1Size.api_name = "bid1Size"
        self.OpenInterest.api_name = "openInterest"
        self.OpenInterestValue.api_name = "openInterestValue"


class CandleBybit(ICandle):
    def __init__(self):
        super().__init__()
        self.Time.api_name = "startTime"
        self.Open.api_name = "openPrice"
        self.High.api_name = "highPrice"
        self.Low.api_name = "lowPrice"
        self.Close.api_name = "closePrice"
        self.Volume.api_name = "volume"
        self.Turnover.api_name = "turnover"


class CandleTickerBybit(ICandleTicker):
    def __init__(self):
        super().__init__()
        self.Time.api_name = "timestamp"
        self.Start.api_name = "start"
        self.End.api_name = "end"
        self.Open.api_name = "open"
        self.High.api_name = "high"
        self.Low.api_name = "low"
        self.Close.api_name = "close"
        self.Volume.api_name = "volume"
        self.Turnover.api_name = "turnover"


class OrderBookBybit(IOrderBook):
    def __init__(self):
        super().__init__()
        self.Time.api_name = "ts"
        self.Asks.api_name = "a"
        self.Bids.api_name = "b"


class MapBybit(IMap):
    def __init__(self):
        super().__init__()
        self.ticker = TickerBybit()
        self.candle = CandleBybit()
        self.candle_ticker = CandleTickerBybit()
        self.order_book = OrderBookBybit()

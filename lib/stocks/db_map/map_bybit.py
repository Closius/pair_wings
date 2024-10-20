from lib.stocks.db_map.map_interface import ITicker, ICandle, ICandleTicker, IOrderBook, IPosition, IMap


class TickerBybit(ITicker):
    def __init__(self):
        super().__init__()
        self.Time.api_name = "ts"
        self.MarkPrice.api_name = "markPrice"
        self.Ask1Size.api_name = "ask1Size"
        self.Bid1Size.api_name = "bid1Size"
        self.OpenInterest.api_name = "openInterest"
        self.OpenInterestValue.api_name = "openInterestValue"
        self.FundingRate.api_name = "fundingRate"

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


class PositionBybit(IPosition):
    def __init__(self, api_response_type="http"):
        """

        :param api_response_type: "websocket", "http"
        """
        super().__init__()
        self.Pair.api_name = "symbol"
        self.CreatedTime.api_name = "createdTime"
        self.UpdatedTime.api_name = "updatedTime"
        self.Side.api_name = "side"
        self.Size.api_name = "size"
        if api_response_type == "http":
            self.AvgPrice.api_name = "avgPrice"
        elif api_response_type == "websocket":
            self.AvgPrice.api_name = "entryPrice"
        self.Leverage.api_name = "leverage"
        self.MarkPrice_.api_name = "markPrice"
        self.StopLoss.api_name = "stopLoss"
        self.TakeProfit.api_name = "takeProfit"
        self.Unrealized_PL_Money.api_name = None  # calculated
        self.ROI_percent.api_name = None  # calculated
        self.Closed_PL_Money.api_name = None  # calculated

class MapBybit(IMap):
    def __init__(self):
        super().__init__()
        self.ticker = TickerBybit()
        self.candle = CandleBybit()
        self.candle_ticker = CandleTickerBybit()
        self.order_book = OrderBookBybit()
        self.position = PositionBybit()

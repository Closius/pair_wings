"""
Mapping between Stock API and the local database

in the implementation you have to set "api_name" for each field:

> Note: The order of fields might be important if the Stock API
        returns list of values (not a dict with field names)

```
class TickerBybit(ITicker):
    def __init__(self):
        super().__init__()
        self.Time.api_name = "ts"
        self.MarkPrice.api_name = "markPrice"
        self.Ask1Size.api_name = "ask1Size"
        ...
```

and use only implementation of IMap:

```
class MapBybit(IMap):
    def __init__(self):
        super().__init__()
        self.ticker = TickerBybit()
        ...
```
"""
import logging

import pandas as pd
import numpy as np

_NDARRAY_DB_TYPE = "NDARRAY"


class _Field:
    def __init__(self, db_name, db_type, df_type, api_name=None):
        self.db_name = db_name  # name of the column in database
        self.db_type = db_type  # type (and key words nearby for table creating) in database
        self.df_type = df_type  # DataFrame column type
        self.api_name = api_name  # name in stock API


class _base:

    def __init__(self):
        # self.init_fields = [c for c in self.__dict__.values() if isinstance(c, _Field)]
        # Order is maintained
        self.init_fields = {k: v for k, v in self.__dict__.items() if isinstance(v, _Field)}

    def get_names_types_for_DB(self):
        s = []
        for i in range(len(self.get_db_names())):
            s.append(f"{self.get_db_names()[i]} {self.get_db_types()[i]}")
        return ",".join(s)
    def get_db_names(self):
        return [c.db_name for c in self.init_fields.values()]
    def get_db_types(self):
        return [c.db_type for c in self.init_fields.values()]
    def get_api_names(self):
        return [c.api_name for c in self.init_fields.values()]
    def to_dataframe(self):
        data = {}
        data_type = {}
        for f_name in self.init_fields.keys():
            data[f_name] = self.__dict__[f_name] if not isinstance(self.__dict__[f_name], _Field) else None
            data_type[f_name] = self.init_fields[f_name].df_type
        df = pd.DataFrame([data]).astype(data_type)
        return df


class IInstrumentInfo(_base):
    """
    Taker - open/close by market
    Maker - open/close by limit (add liquidity)
    """
    def __init__(self):
        self.MaxLeverage = _Field("MaxLeverage", "REAL", "int16", NotImplemented)
        # float value accuracy, for USDT
        self.PriceScale = _Field("PriceScale", "REAL", "int16", NotImplemented)
        # float value accuracy, for BTC
        self.QtyScale = _Field("QtyScale", "REAL", "int16", NotImplemented)
        self.TakerFeeRate = _Field("TakerFeeRate", "REAL", "float64", NotImplemented)
        self.MakerFeeRate = _Field("MakerFeeRate", "REAL", "float64", NotImplemented)
        self.MinOrderQty = _Field("MinOrderQty", "REAL", "float64", NotImplemented)
        self.OrderQtyStep = _Field("OrderQtyStep", "REAL", "float64", NotImplemented)
        # a min price of the amount that can be placed in a single order
        self.MinOrderValue = _Field("MinOrderValue", "REAL", "float64", NotImplemented)
        super().__init__()


class ITicker(_base):
    """
        Fields after set:
            'Time': datetime.datetime(2024, 10, 2, 22, 54, 17, 928000),
            'MarkPrice': 3259.94,
            'Ask1Size': 0.155,
            'Bid1Size': 4199.144,
            'OpenInterest': 1224249.628,
            'OpenInterestValue': 3990980332.30
            'FundingRate': 0.05
    """
    def __init__(self):
        self.Time = _Field("Time", "TIMESTAMP UNIQUE", "datetime64[ns]", NotImplemented)
        self.MarkPrice = _Field("MarkPrice", "REAL", "float64", NotImplemented)
        self.Ask1Size = _Field("Ask1Size", "REAL", "float64", NotImplemented)
        self.Bid1Size = _Field("Bid1Size", "REAL", "float64", NotImplemented)
        self.OpenInterest = _Field("OpenInterest", "REAL", "float64", NotImplemented)
        self.OpenInterestValue = _Field("OpenInterestValue", "REAL", "float64", NotImplemented)
        self.FundingRate = _Field("FundingRate", "REAL", "float64", NotImplemented)
        super().__init__()


class ICandle(_base):
    """
    Historical candles. Finished

    Fields after set:
        'Time': datetime.datetime(2024, 9, 16, 19, 15),
        'Open': 57566.6,
        'High': 57718.8,
        'Low': 57535.1,
        'Close': 57569.7,
        'Volume': 614.993,
        'Turnover': 35447184.1698
    """
    def __init__(self):
        self.Time = _Field("Time", "TIMESTAMP UNIQUE", "datetime64[ns]", NotImplemented)
        self.Open = _Field("Open", "REAL", "float64", NotImplemented)
        self.High = _Field("High", "REAL", "float64", NotImplemented)
        self.Low = _Field("Low", "REAL", "float64", NotImplemented)
        self.Close = _Field("Close", "REAL", "float64", NotImplemented)
        self.Volume = _Field("Volume", "REAL", "float64", NotImplemented)
        self.Turnover = _Field("Turnover", "REAL", "float64", NotImplemented)
        super().__init__()


class ICandleTicker(_base):
    """
    Stream of candles. Finished

    Fields after set:
        'Time': datetime.datetime(2024, 10, 2, 23, 20, 41, 655000),
        'Start': datetime.datetime(2024, 10, 2, 23, 20),
        'End': datetime.datetime(2024, 10, 2, 23, 24, 59, 999000),
        'Open': 55239.6,
        'High': 55440,
        'Low': 53750,
        'Close': 55440,
        'Volume': 2382.393,
        'Turnover': 132078946.7517
    """
    def __init__(self):
        self.Time = _Field("Time", "TIMESTAMP UNIQUE", "datetime64[ns]", NotImplemented)
        self.Start = _Field("Start", "TIMESTAMP", "datetime64[ns]", NotImplemented)  # when the candle starts
        self.End = _Field("End", "TIMESTAMP", "datetime64[ns]", NotImplemented)
        self.Open = _Field("Open", "REAL", "float64", NotImplemented)
        self.High = _Field("High", "REAL", "float64", NotImplemented)
        self.Low = _Field("Low", "REAL", "float64", NotImplemented)
        self.Close = _Field("Close", "REAL", "float64", NotImplemented)
        self.Volume = _Field("Volume", "REAL", "float64", NotImplemented)
        self.Turnover = _Field("Turnover", "REAL", "float64", NotImplemented)
        super().__init__()


class IOrderBook(_base):
    """
    Fields after set:
        'Time': datetime.datetime(2024, 10, 2, 23, 20, 39, 873000),
        'Asks': np.array(shape=(50, 2)),  # [price, volume], order: price lower -> higher
        'Bids': np.array(shape=(50, 2)),  # [price, volume], order: price higher -> lower
    """
    def __init__(self):
        self.Time = _Field("Time", "TIMESTAMP UNIQUE", "datetime64[ns]", NotImplemented)
        self.Bids = _Field("Bids", _NDARRAY_DB_TYPE, "object", NotImplemented)
        self.Asks = _Field("Asks", _NDARRAY_DB_TYPE, "object", NotImplemented)
        super().__init__()


class IPosition(_base):
    """
    If 'Size' == 0 -> Position is closed

    Fields after set:
        'CreatedTime': datetime.datetime(2024, 10, 2, 23, 20, 39, 873000),
        'UpdatedTime': datetime.datetime(2024, 10, 2, 23, 20, 39, 873000),
        'Side': "SHORT"/"LONG",
        'Size': float,
        'Profit_': float,
        'MarkPrice_': float,
        'StopLoss': float | None,
        'TakeProfit': float | None,
    """
    def __init__(self):
        self.Pair = _Field("Pair", "TEXT", "string", NotImplemented)
        self.CreatedTime = _Field("CreatedTime", "TIMESTAMP", "datetime64[ns]", NotImplemented)
        self.UpdatedTime = _Field("UpdatedTime", "TIMESTAMP", "datetime64[ns]", NotImplemented)
        self.Side = _Field("Side", "TEXT", "string", NotImplemented)
        self.Size = _Field("Size", "REAL", "float64", NotImplemented)
        self.AvgPrice = _Field("AvgPrice", "REAL", "float64", NotImplemented)
        self.Leverage = _Field("Leverage", "REAL", "float64", NotImplemented)
        self.MarkPrice_ = _Field("MarkPrice_", "REAL", "float64", NotImplemented)
        self.StopLoss = _Field("StopLoss", "REAL", "float64", NotImplemented)
        self.TakeProfit = _Field("TakeProfit", "REAL", "float64", NotImplemented)
        # PL without any fees
        self.Unrealized_PL_Money = _Field("Unrealized_PL_Money", "REAL",  "float64", NotImplemented)
        # ROI
        self.ROI_percent = _Field("ROI_percent", "REAL",  "float64", NotImplemented)
        # How much I earn on my wallet
        self.Closed_PL_Money = _Field("Closed_PL_Money", "REAL",  "float64", NotImplemented)
        super().__init__()


class IMap:
    def __init__(self):
        self.ticker = ITicker()
        self.candle = ICandle()
        self.candle_ticker = ICandle()
        self.order_book = IOrderBook()
        self.position = IPosition()

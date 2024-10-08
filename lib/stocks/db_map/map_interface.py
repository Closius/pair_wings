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
import uuid


_NDARRAY_DB_TYPE = "NDARRAY"

class _Field:
    def __init__(self, db_name, db_type, api_name=None):
        self.db_name = db_name  # name of the column in database
        self.db_type = db_type  # type (and key words nearby for table creating) in database
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


class ITicker(_base):
    """
        Fields after set:
            'Time': datetime.datetime(2024, 10, 2, 22, 54, 17, 928000),
            'MarkPrice': '3259.94',
            'Ask1Size': '0.155',
            'Bid1Size': '4199.144',
            'OpenInterest': '1224249.628',
            'OpenInterestValue': '3990980332.30'
    """
    def __init__(self):
        self.Time = _Field("Time", "TIMESTAMP UNIQUE", NotImplemented)
        self.MarkPrice = _Field("MarkPrice", "REAL", NotImplemented)
        self.Ask1Size = _Field("Ask1Size", "REAL", NotImplemented)
        self.Bid1Size = _Field("Bid1Size", "REAL", NotImplemented)
        self.OpenInterest = _Field("OpenInterest", "REAL", NotImplemented)
        self.OpenInterestValue = _Field("OpenInterestValue", "REAL", NotImplemented)
        super().__init__()


class ICandle(_base):
    """
    Historical candles. Finished

    Fields after set:
        'Time': datetime.datetime(2024, 9, 16, 19, 15),
        'Open': '57566.6',
        'High': '57718.8',
        'Low': '57535.1',
        'Close': '57569.7',
        'Volume': '614.993',
        'Turnover': '35447184.1698'
    """
    def __init__(self):
        self.Time = _Field("Time", "TIMESTAMP UNIQUE", NotImplemented)
        self.Open = _Field("Open", "REAL", NotImplemented)
        self.High = _Field("High", "REAL", NotImplemented)
        self.Low = _Field("Low", "REAL", NotImplemented)
        self.Close = _Field("Close", "REAL", NotImplemented)
        self.Volume = _Field("Volume", "REAL", NotImplemented)
        self.Turnover = _Field("Turnover", "REAL", NotImplemented)
        super().__init__()


class ICandleTicker(_base):
    """
    Stream of candles. Finished

    Fields after set:
        'Time': datetime.datetime(2024, 10, 2, 23, 20, 41, 655000),
        'Start': datetime.datetime(2024, 10, 2, 23, 20),
        'End': datetime.datetime(2024, 10, 2, 23, 24, 59, 999000),
        'Open': '55239.6',
        'High': '55440',
        'Low': '53750',
        'Close': '55440',
        'Volume': '2382.393',
        'Turnover': '132078946.7517'
    """
    def __init__(self):
        self.Time = _Field("Time", "TIMESTAMP UNIQUE", NotImplemented)
        self.Start = _Field("Start", "TIMESTAMP", NotImplemented)  # when the candle starts
        self.End = _Field("End", "TIMESTAMP", NotImplemented)
        self.Open = _Field("Open", "REAL", NotImplemented)
        self.High = _Field("High", "REAL", NotImplemented)
        self.Low = _Field("Low", "REAL", NotImplemented)
        self.Close = _Field("Close", "REAL", NotImplemented)
        self.Volume = _Field("Volume", "REAL", NotImplemented)
        self.Turnover = _Field("Turnover", "REAL", NotImplemented)
        super().__init__()


class IOrderBook(_base):
    """
    Fields after set:
        'Time': datetime.datetime(2024, 10, 2, 23, 20, 39, 873000),
        'Asks': np.array(shape=(50, 2)),  # [price, volume], order: price lower -> higher
        'Bids': np.array(shape=(50, 2)),  # [price, volume], order: price higher -> lower
    """
    def __init__(self):
        self.Time = _Field("Time", "TIMESTAMP UNIQUE", NotImplemented)
        self.Bids = _Field("Bids", _NDARRAY_DB_TYPE, NotImplemented)
        self.Asks = _Field("Asks", _NDARRAY_DB_TYPE, NotImplemented)
        super().__init__()


class IPosition(_base):
    """
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
        self.CreatedTime = _Field("CreatedTime", "TIMESTAMP", NotImplemented)
        self.UpdatedTime = _Field("UpdatedTime", "TIMESTAMP", NotImplemented)
        self.Side = _Field("Side", "TEXT", NotImplemented)
        self.Size = _Field("Size", "REAL", NotImplemented)
        # Netto, what you earn if close by market
        self.Profit_ = _Field("Profit_", "REAL", NotImplemented)
        self.MarkPrice_ = _Field("MarkPrice_", "TEXT", NotImplemented)
        self.StopLoss = _Field("StopLoss", "REAL", NotImplemented)
        self.TakeProfit = _Field("TakeProfit", "REAL", NotImplemented)
        super().__init__()


class IMap:
    def __init__(self):
        self.ticker = ITicker()
        self.candle = ICandle()
        self.candle_ticker = ICandle()
        self.order_book = IOrderBook()
        self.position = IPosition()

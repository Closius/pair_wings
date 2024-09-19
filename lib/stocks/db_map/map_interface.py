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

_NDARRAY_DB_TYPE = "NDARRAY"

class _Field:
    def __init__(self, db_name, db_type, api_name=None):
        self.db_name = db_name  # name of the column in database
        self.db_type = db_type  # type (and key words nearby for table creating) in database
        self.api_name = api_name  # name in stock API

class _base:

    def get_names_types_for_DB(self):
        s = []
        for i in range(len(self.get_db_names())):
            s.append(f"{self.get_db_names()[i]} {self.get_db_types()[i]}")
        return ",".join(s)
    def get_db_names(self):
        return [c.db_name for c in self.__dict__.values() if isinstance(c, _Field)]
    def get_db_types(self):
        return [c.db_type for c in self.__dict__.values() if isinstance(c, _Field)]
    def get_api_names(self):
        return [c.api_name for c in self.__dict__.values() if isinstance(c, _Field)]


class ITicker(_base):
    def __init__(self):
        self.Time = _Field("Time", "TIMESTAMP UNIQUE", NotImplemented)
        self.MarkPrice = _Field("MarkPrice", "REAL", NotImplemented)
        self.Ask1Size = _Field("Ask1Size", "REAL", NotImplemented)
        self.Bid1Size = _Field("Bid1Size", "REAL", NotImplemented)
        self.OpenInterest = _Field("OpenInterest", "REAL", NotImplemented)
        self.OpenInterestValue = _Field("OpenInterestValue", "REAL", NotImplemented)


class ICandle(_base):
    def __init__(self):
        self.Time = _Field("Time", "TIMESTAMP UNIQUE", NotImplemented)
        self.Open = _Field("Open", "REAL", NotImplemented)
        self.High = _Field("High", "REAL", NotImplemented)
        self.Low = _Field("Low", "REAL", NotImplemented)
        self.Close = _Field("Close", "REAL", NotImplemented)
        self.Volume = _Field("Volume", "REAL", NotImplemented)
        self.Turnover = _Field("Turnover", "REAL", NotImplemented)


class IOrderBook(_base):
    def __init__(self):
        self.Time = _Field("Time", "TIMESTAMP UNIQUE", NotImplemented)
        self.Bids = _Field("Bids", _NDARRAY_DB_TYPE, NotImplemented)
        self.Asks = _Field("Asks", _NDARRAY_DB_TYPE, NotImplemented)


class IMap:
    def __init__(self):
        self.ticker = ITicker()
        self.candle = ICandle()
        self.order_book = IOrderBook()

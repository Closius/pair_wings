# StateCollection() -> Iterator of [{"stock_A": {State}, "stock_B": {State}, ...}, ]
# State()
#
#
# The strategy is working in the loop of StateCollection()
#
# StateCollection is waiting for the date from the Stock(s) and updates
# the State(s) (push updates into the queue). In parallel
#
#
# The iterator state object of the current period of time
# Every time when any of the information is received from the stock
# - the state object returns
#
# State has the same fields as Map
#
# State.ticker = ITicker()
# State.candle = ICandle()
# State.candle_ticker = ICandleTicker()
# State.order_book = IOrderBook()
#
# State can be also a slice. State type: scalar, slice
#
# StateCollection object can contain the information about
# multiple stocks, for example in a dicrionary
# {"stock_A": {State}, "stock_B": {State}, ...}
#
#
# StateCollection.whats_new() - returns what
# was changed in a list
#
#
# StateCollection.remember(period: datetime) - remember "period" of
# last history, so this information can be available from the strategy
#
# StateCollection.return_as_dataframe(start: datetime, end: datetime | None)
#

import pandas as pd

from lib.map_interface import IMap


class State(IMap):

    def __init__(self, **kwargs):
        super().__init__()
        self._remember_last_N = None
        self._dataframes = {k: v.to_dataframe() for k, v in IMap().__dict__.items()}
        self.append_single_snapshot(**kwargs)
        # The first snapshot is always full of Nones
        for k in self._dataframes.keys():
            self._dataframes[k] = self._dataframes[k].drop(index=[0])

    def append_single_snapshot(self, **kwargs):
        for field_name in IMap().__dict__.keys():
            field_obj = IMap().__dict__[field_name] if field_name not in kwargs else kwargs[field_name]
            if field_name not in self.__dict__.keys():
                raise ValueError(f"field `{field_name}` is not exist in IMap")
            if not isinstance(field_obj, type(IMap().__dict__[field_name])):
                raise ValueError(f"field `{field_name}` type mismatch: sent `{type(field_obj)}` "
                                 f"required: `{type(self.__dict__[field_name])}`")

            self._dataframes[field_name] = pd.concat([self._dataframes[field_name], field_obj.to_dataframe()],
                                                     ignore_index=True)
            if self._remember_last_N:
                self._dataframes[field_name].drop(
                    self._dataframes[field_name].index[:-self._remember_last_N], inplace=True)

    def __getitem__(self, item):
        for k in self._dataframes.keys():
            self._dataframes[k] = self._dataframes[k].drop(index=[0])
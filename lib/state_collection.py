# StateCollection() -> Iterator of [{"stock_A": {State}, "stock_B": {State}, ...}, ]
# State()
#
#
# The strategy is working in the loop of StateCollection()
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

# The iterator state object of the current period of time
# Every time when any of the information is received from the stock
# - the state object returns
#
# State object can contain the information about
# multiple stocks, for example in a dicrionary
# {"stock_A": {State}, "stock_B": {State}, ...}
#
#
# State.whats_new() - returns what
# was changed in a list
#
#
# State.remember(period: datetime) - remember "period" of
# last history, so this information can be available from the strategy
#
#
# The strategy is
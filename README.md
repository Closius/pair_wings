Pairwings
=========

Pairwings (or PW) is a framework for developing, testing and running the trading strategies. Features:

- backends. The interface to the stock exchange API allows to easy implement the plug-in 
  to APIs of the different stock exchanges 
- data mining. Collect the data from the stock exchange and store in a local the SQL database. 
  With easy connect to the new backend and develop yours
- backtesting. Test the strategy based on the collected data stored in a local SQL database.
- develop the strategy. The interface to the Strategy object. 
  The implementation of that interface allows to use this strategy for backtesting and 
  for a real trading in the single framework. 
- trade. Run the strategy for a real trading.

Limitations & Remarks
---------------------

* Only Perpetual futures trading. 
* All orders are executed by market price. 
  See more in the doc of methods `stock.open_modify_SHORT_LONG()` `stock.close_SHORT_LONG()`
* No hadge trading - can hold only SHORT or LONG at one time
* Cross margin only

* Only one position for the pair. With same pair in Derivatives/Futures trading exchanges 
don't open several positions for individual position, in fact new position's quantity 
gets added to the existing position, so if you had BTCUSDT position opened 
with quantity 2, and you open a new position with quantity 3, the existing 
position's quantity will be added to 5 instead of opening a new position. 
Only positions with different pairs are created individually.


Roadmap
-------

1. Finish the implementation of ByBit backend which allows to finish implementations of the data maps.
   1. next TODO: think about: remember last N (by datetime duration?) States (lib/state_collection.py)
   2. next TODO: implement State get state by datetime or get range (lib/state_collection.py)
2. GUI
3. Use python.decimal.Decimal instead of float for money related values
4. Check TODO in the code
5. Write a simple MA strategy.
6. Implement the stock exchange based on the data from the local SQL database
7. Develop the Strategy runner. Test on the local SQL database
8. Write pytest. Add CI
9. Add to PyPi index
10. The documentation

Open questions: 

1. Should I use SqlAlchemy ORM ?
2. Should I try https://github.com/ccxt/ccxt ?  
3. TradingView plots in Python https://github.com/louisnw01/lightweight-charts-python or https://github.com/domarm-comat/pglive?tab=readme-ov-file

Prerequisites
-------------

Python 3.12

`python.exe -m pip install -r requirements.txt`

qt designer: https://build-system.fman.io/qt-designer-download

Quick start
-----------

1. Run the program `python.exe main.py`
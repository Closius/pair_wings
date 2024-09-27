Pairwings
=========

Pairwings or PW is a framework for developing the trading strategies. It provides such capabilities as:

- backends. The interface to the stock exchange API allows to easy implement the plug-in 
  to APIs of the different stock exchanges 
- data mining. Collect the data from the stock exchange and store in a local the SQL database. 
  With easy connect to the new backend and develop yours
- backtesting. Test the strategy based on the collected data stored in a local SQL database.
- develop the strategy. The interface to the Strategy object. 
  The implementation of that interface allows to use this strategy for backtesting and 
  for a real trading in the single framework. 
- trade. Run the strategy for a real trading.

Roadmap
-------

1. Finish the implementation of ByBit backend which allows to finish implementations of the data maps.
2. Write a simple MA strategy.
3. Implement the stock exchange based on the data from the local SQL database
4. Develop the Strategy runner. Test on the local SQL database
5. Write pytest. Add CI
6. Add to PyPi index
7. The documentation

Prerequisites
-------------

Python 3.12

`python.exe -m pip install -r requirements.txt`

Quick start
-----------

1. Run the program `python.exe main.py`
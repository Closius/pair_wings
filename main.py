import logging
import threading

from lib import data_show, data_collector, utils, random_trade

from lib.stocks.stock_bybit import StockBybit
from lib.stocks.db_map.map_bybit import MapBybit


def main():
    log = utils.setup_logger("", "pybit.log", level=logging.INFO, stream=True)

    # pair = "WIFUSDT"
    pair = "BTCUSDT"

    log.info("==========================")
    log.info("Choose your destiny:")
    log.info("1 - Collect streams: candle, ticker, order book")
    log.info("2 - Collect candles")
    log.info("3 - Show candles")
    log.info("4 - Read order books")
    log.info("5 - Read stream candles")
    log.info("6 - Trade demo: open SHORT wait close")
    log.info("7 - Trade demo: get position status")
    log.info("8 - Trade demo: statistical error")
    log.info("9 - Get all pairs")
    log.info("10 - Quit")
    log.info("")
    log.info(f"pair: {pair}")
    log.info("")
    r = input()
    log.info(r)
    map = MapBybit()
    stock = StockBybit(map=map, account_name="pair_wings_demo",
                       api_secrets_file="bybit_api_secret.json",
                       settings_file="bybit_settings.json")
    # stock = StockBybit(map=map)
    db_filepath = "main.db"
    event = threading.Event()
    if r == "1":
        dc = data_collector.DataCollector(stock, db_filepath, map)
        dc.collect_stream_tickers(pair=pair, stop_event=event, recreate=True)
        dc.collect_stream_candles_ticker(pair=pair, interval="5", stop_event=event, recreate=True)
        dc.collect_stream_order_book(pair=pair, stop_event=event, recreate=True)

        log.info("==========================")
        log.info("Press Enter to Stop collection")
        input()
        event.set()
        log.info("Interrupted")

    elif r == "2":
        dc = data_collector.DataCollector(stock, db_filepath, map)
        dc.collect_history_candles(pair=pair, interval="5",
                                   start='16.09.2024 19:00:00,00',
                                   end=None,
                                   recreate=True)

    elif r == "3":
        data_show.draw_candles(db_filepath, pair=pair, map=map)
    elif r == "4":
        data_show.read_order_book(db_filepath, pair=pair, map=map)
    elif r == "5":
        data_show.read_stream_candles(db_filepath, pair=pair, interval="5", map=map)
    elif r == "6":
        random_trade.open_add_position(stock, pair=pair, side="SHORT", percent_from_deposit=1, qty=0.01,
                    wait_for_add_second=None, add_qty=0.01)

        # time.sleep(20)
        # r = random_trade.close_position(stock, pair=pair, amount_percent=100, verbose=True)
    elif r == "7":
        position = stock.get_position_status(pair=pair, verbose=True)
    elif r == "8":
        # 10 because of connections limit
        pairs = ['ACEUSDT', 'BTCUSDT', 'COREUSDT', 'DASHUSDT', 'EOSUSDT', 'ETHUSDT', 'HMSTRUSDT',
            'MNTUSDT', 'SOLUSDT', 'MONUSDT'] #, 'WIFUSDT', 'RAREUSDT']

        # pairs = ['10000000AIDOGEUSDT', '1000000BABYDOGEUSDT', '1000000MOGUSDT', '1000000PEIPEIUSDT', '10000COQUSDT',
        #  '10000LADYSUSDT', '10000SATSUSDT', '10000WENUSDT', '10000WHYUSDT', '1000APUUSDT', '1000BEERUSDT',
        #  '1000BONKUSDT', '1000BTTUSDT', '1000CATSUSDT', '1000CATUSDT', '1000FLOKIUSDT', '1000LUNCUSDT', '1000MUMUUSDT',
        #  '1000NEIROCTOUSDT', '1000PEPEPERP', '1000PEPEUSDT', '1000RATSUSDT', '1000TURBOUSDT', '1000XECUSDT', '1CATUSDT',
        #  '1INCHUSDT', 'A8USDT', 'AAVEUSDT', 'ACEUSDT', 'ACHUSDT', 'ADAUSDT', 'AERGOUSDT', 'AEROUSDT', 'AEVOPERP',
        #  'AEVOUSDT', 'AGIUSDT', 'AGLDUSDT', 'AIOZUSDT', 'AIUSDT', 'AKROUSDT', 'AKTUSDT', 'ALEOUSDT', 'ALGOUSDT',
        #  'ALICEUSDT', 'ALPACAUSDT', 'ALPHAUSDT', 'ALTUSDT', 'AMBUSDT', 'ANKRUSDT', 'APEUSDT', 'API3USDT', 'APTUSDT',
        #  'ARBPERP', 'ARBUSDT', 'ARKMUSDT', 'ARKUSDT', 'ARPAUSDT', 'ARUSDT', 'ASTRUSDT', 'ATAUSDT', 'ATHUSDT',
        #  'ATOMUSDT', 'AUCTIONUSDT', 'AUDIOUSDT', 'AVAILUSDT', 'AVAXUSDT', 'AXLUSDT', 'AXSUSDT', 'BADGERUSDT',
        #  'BAKEUSDT', 'BALUSDT', 'BANANAUSDT', 'BANDUSDT', 'BATUSDT', 'BBUSDT', 'BCHUSDT', 'BEAMUSDT', 'BELUSDT',
        #  'BENDOGUSDT', 'BICOUSDT', 'BIGTIMEUSDT', 'BLASTUSDT', 'BLURUSDT', 'BLZUSDT', 'BNBPERP', 'BNBUSDT', 'BNTUSDT',
        #  'BNXUSDT', 'BOBAUSDT', 'BOMEUSDT', 'BONDUSDT', 'BRETTUSDT', 'BSVUSDT', 'BSWUSDT', 'BTC-01NOV24', 'BTC-18OCT24',
        #  'BTC-25OCT24', 'BTC-26SEP25', 'BTC-27DEC24', 'BTC-27JUN25', 'BTC-28MAR25', 'BTC-29NOV24', 'BTCPERP', 'BTCUSDT',
        #  'C98USDT', 'CAKEUSDT', 'CATIUSDT', 'CELOUSDT', 'CELRUSDT', 'CETUSUSDT', 'CFXUSDT', 'CHESSUSDT', 'CHRUSDT',
        #  'CHZUSDT', 'CKBUSDT', 'CLOUDUSDT', 'COMBOUSDT', 'COMPUSDT', 'COREUSDT', 'COSUSDT', 'COTIUSDT', 'CROUSDT',
        #  'CRVUSDT', 'CTCUSDT', 'CTKUSDT', 'CTSIUSDT', 'CVCUSDT', 'CVXUSDT', 'CYBERUSDT', 'DARUSDT', 'DASHUSDT',
        #  'DATAUSDT', 'DEGENUSDT', 'DENTUSDT', 'DEXEUSDT', 'DGBUSDT', 'DODOUSDT', 'DOGEPERP', 'DOGEUSDT', 'DOGSUSDT',
        #  'DOGUSDT', 'DOP1USDT', 'DOTUSDT', 'DRIFTUSDT', 'DUSKUSDT', 'DYDXUSDT', 'DYMUSDT', 'EDUUSDT', 'EGLDUSDT',
        #  'EIGENUSDT', 'ENAUSDT', 'ENJUSDT', 'ENSUSDT', 'EOSUSDT', 'ETCPERP', 'ETCUSDT', 'ETH-01NOV24', 'ETH-18OCT24',
        #  'ETH-25OCT24', 'ETH-26SEP25', 'ETH-27DEC24', 'ETH-27JUN25', 'ETH-28MAR25', 'ETH-29NOV24', 'ETHBTCUSDT',
        #  'ETHFIPERP', 'ETHFIUSDT', 'ETHPERP', 'ETHUSDT', 'ETHWUSDT', 'FBUSDT', 'FDUSDUSDT', 'FIDAUSDT', 'FILUSDT',
        #  'FIOUSDT', 'FIREUSDT', 'FITFIUSDT', 'FLMUSDT', 'FLOWUSDT', 'FLRUSDT', 'FLUXUSDT', 'FORTHUSDT', 'FOXYUSDT',
        #  'FTMUSDT', 'FTNUSDT', 'FUNUSDT', 'FXSUSDT', 'GALAUSDT', 'GASUSDT', 'GFTUSDT', 'GLMRUSDT', 'GLMUSDT', 'GMEUSDT',
        #  'GMTUSDT', 'GMXUSDT', 'GNOUSDT', 'GODSUSDT', 'GOMININGUSDT', 'GRTUSDT', 'GTCUSDT', 'GUSDT', 'HBARUSDT',
        #  'HFTUSDT', 'HIFIUSDT', 'HIGHUSDT', 'HMSTRUSDT', 'HNTUSDT', 'HOOKUSDT', 'HOTUSDT', 'ICPUSDT', 'ICXUSDT',
        #  'IDEXUSDT', 'IDUSDT', 'ILVUSDT', 'IMXUSDT', 'INJUSDT', 'IOSTUSDT', 'IOTAUSDT', 'IOTXUSDT', 'IOUSDT',
        #  'JASMYUSDT', 'JOEUSDT', 'JSTUSDT', 'JTOUSDT', 'JUPUSDT', 'KASUSDT', 'KAVAUSDT', 'KDAUSDT', 'KEYUSDT',
        #  'KLAYUSDT', 'KMNOUSDT', 'KNCUSDT', 'KSMUSDT', 'L3USDT', 'LAIUSDT', 'LDOUSDT', 'LEVERUSDT', 'LINAUSDT',
        #  'LINKUSDT', 'LISTAUSDT', 'LITUSDT', 'LOOKSUSDT', 'LPTUSDT', 'LQTYUSDT', 'LRCUSDT', 'LSKUSDT', 'LTCUSDT',
        #  'LTOUSDT', 'LUNA2USDT', 'MAGICUSDT', 'MANAUSDT', 'MANEKIUSDT', 'MANTAUSDT', 'MASAUSDT', 'MASKUSDT',
        #  'MAVIAUSDT', 'MAVUSDT', 'MAXUSDT', 'MBLUSDT', 'MBOXUSDT', 'MDTUSDT', 'MEMEUSDT', 'MERLUSDT', 'METISUSDT',
        #  'MEWUSDT', 'MINAUSDT', 'MKRUSDT', 'MNTPERP', 'MNTUSDT', 'MOBILEUSDT', 'MOCAUSDT', 'MONUSDT', 'MOODENGUSDT',
        #  'MOTHERUSDT', 'MOVRUSDT', 'MTLUSDT', 'MYRIAUSDT', 'MYROUSDT', 'NEARUSDT', 'NEIROETHUSDT', 'NEOUSDT', 'NFPUSDT',
        #  'NKNUSDT', 'NMRUSDT', 'NOTPERP', 'NOTUSDT', 'NTRNUSDT', 'NULSUSDT', 'NYANUSDT', 'OGNUSDT', 'OGUSDT', 'OMGUSDT',
        #  'OMNIUSDT', 'OMUSDT', 'ONDOPERP', 'ONDOUSDT', 'ONEUSDT', 'ONGUSDT', 'ONTUSDT', 'OPPERP', 'OPUSDT', 'ORBSUSDT',
        #  'ORCAUSDT', 'ORDERUSDT', 'ORDIPERP', 'ORDIUSDT', 'ORNUSDT', 'OSMOUSDT', 'OXTUSDT', 'PAXGUSDT', 'PENDLEUSDT',
        #  'PENGUSDT', 'PEOPLEUSDT', 'PERPUSDT', 'PHAUSDT', 'PHBUSDT', 'PIRATEUSDT', 'PIXELUSDT', 'PIXFIUSDT', 'POLPERP',
        #  'POLUSDT', 'POLYXUSDT', 'PONKEUSDT', 'POPCATPERP', 'POPCATUSDT', 'PORTALUSDT', 'POWRUSDT', 'PRCLUSDT',
        #  'PRIMEUSDT', 'PROMUSDT', 'PYRUSDT', 'PYTHUSDT', 'QIUSDT', 'QNTUSDT', 'QTUMUSDT', 'QUICKUSDT', 'RADUSDT',
        #  'RAREUSDT', 'RAYDIUMUSDT', 'RDNTUSDT', 'REEFUSDT', 'RENDERUSDT', 'RENUSDT', 'REQUSDT', 'REZUSDT', 'RIFUSDT',
        #  'RLCUSDT', 'RONUSDT', 'ROSEUSDT', 'RPLUSDT', 'RSRUSDT', 'RSS3USDT', 'RUNEUSDT', 'RVNUSDT', 'SAFEUSDT',
        #  'SAGAUSDT', 'SANDUSDT', 'SCAUSDT', 'SCRTUSDT', 'SCRUSDT', 'SCUSDT', 'SEIUSDT', 'SFPUSDT', 'SHIB1000PERP',
        #  'SHIB1000USDT', 'SILLYUSDT', 'SKLUSDT', 'SLERFUSDT', 'SLFUSDT', 'SLPUSDT', 'SNTUSDT', 'SNXUSDT', 'SOL-01NOV24',
        #  'SOL-18OCT24', 'SOL-25OCT24', 'SOL-29NOV24', 'SOLPERP', 'SOLUSDT', 'SPECUSDT', 'SPELLUSDT', 'SSVUSDT',
        #  'STEEMUSDT', 'STGUSDT', 'STMXUSDT', 'STORJUSDT', 'STPTUSDT', 'STRKPERP', 'STRKUSDT', 'STXUSDT', 'SUIPERP',
        #  'SUIUSDT', 'SUNDOGUSDT', 'SUNUSDT', 'SUPERUSDT', 'SUSHIUSDT', 'SWEATUSDT', 'SXPUSDT', 'SYNUSDT', 'SYSUSDT',
        #  'TAIKOUSDT', 'TAOUSDT', 'THETAUSDT', 'TIAPERP', 'TIAUSDT', 'TLMUSDT', 'TNSRUSDT', 'TOKENUSDT', 'TOMIUSDT',
        #  'TONPERP', 'TONUSDT', 'TRBUSDT', 'TRUUSDT', 'TRXUSDT', 'TUSDT', 'TWTUSDT', 'UMAUSDT', 'UNFIUSDT', 'UNIUSDT',
        #  'USDCUSDT', 'USDEUSDT', 'USTCUSDT', 'UXLINKUSDT', 'VANRYUSDT', 'VELOUSDT', 'VETUSDT', 'VIDTUSDT', 'VOXELUSDT',
        #  'VRAUSDT', 'VTHOUSDT', 'WAVESUSDT', 'WAXPUSDT', 'WIFPERP', 'WIFUSDT', 'WLDPERP', 'WLDUSDT', 'WOOUSDT', 'WUSDT',
        #  'XAIUSDT', 'XCHUSDT', 'XCNUSDT', 'XEMUSDT', 'XLMUSDT', 'XMRUSDT', 'XNOUSDT', 'XRDUSDT', 'XRPPERP', 'XRPUSDT',
        #  'XTZUSDT', 'XVGUSDT', 'XVSUSDT', 'YFIUSDT', 'YGGUSDT', 'ZBCNUSDT', 'ZECUSDT', 'ZENUSDT', 'ZETAUSDT',
        #  'ZEUSUSDT', 'ZILUSDT', 'ZKFUSDT', 'ZKJUSDT', 'ZKUSDT', 'ZROUSDT', 'ZRXUSDT']

        pairs_USDT_only = [pair for pair in pairs if pair.endswith("USDT")]

        number_of_pairs_in_simultaneous_trade = 10
        log.info(f"pairs for test {len(pairs_USDT_only)}: {pairs_USDT_only}")
        log.info(f"number_of_pairs_in_simultaneous_trade: {number_of_pairs_in_simultaneous_trade}")
        log.info(f"")
        random_trade.main(pairs=pairs_USDT_only, stock=stock, num_steps=5,
                          number_of_pairs_in_simultaneous_trade=number_of_pairs_in_simultaneous_trade)

    elif r == "9":
        pairs = stock.get_all_pairs()
        log.info(pairs)

if __name__ == "__main__":
    main()

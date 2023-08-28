import json
from unittest import TestCase
import main
import io


class Test(TestCase):
    default_pair_info_str = '{"symbol": "SOLUSDT", "pair": "SOLUSDT", "contractType": "PERPETUAL", "deliveryDate": ' \
                            '4133404800000, "onboardDate": 1569398400000, "status": "TRADING", "maintMarginPercent": ' \
                            '"2.5000", "requiredMarginPercent": "5.0000", "baseAsset": "SOL", "quoteAsset": "USDT", ' \
                            '"marginAsset": "USDT", "pricePrecision": 4, "quantityPrecision": 0, ' \
                            '"baseAssetPrecision": 8, "quotePrecision": 8, "underlyingType": "COIN", ' \
                            '"underlyingSubType": ["Layer-1"], "settlePlan": 0, "triggerProtect": "0.0500", ' \
                            '"liquidationFee": "0.015000", "marketTakeBound": "0.05", "maxMoveOrderLimit": 10000, ' \
                            '"filters": [{"tickSize": "0.0010", "maxPrice": "6857.0000", "minPrice": "0.4200", ' \
                            '"filterType": "PRICE_FILTER"}, {"filterType": "LOT_SIZE", "minQty": "1", "stepSize": ' \
                            '"1", "maxQty": "1000000"}, {"maxQty": "5000", "stepSize": "1", "filterType": ' \
                            '"MARKET_LOT_SIZE", "minQty": "1"}, {"limit": 200, "filterType": "MAX_NUM_ORDERS"}, ' \
                            '{"limit": 10, "filterType": "MAX_NUM_ALGO_ORDERS"}, {"filterType": "MIN_NOTIONAL", ' \
                            '"notional": "5"}, {"multiplierDown": "0.9500", "filterType": "PERCENT_PRICE", ' \
                            '"multiplierUp": "1.0500", "multiplierDecimal": "4"}], "orderTypes": ["LIMIT", "MARKET", ' \
                            '"STOP", "STOP_MARKET", "TAKE_PROFIT", "TAKE_PROFIT_MARKET", "TRAILING_STOP_MARKET"], ' \
                            '"timeInForce": ["GTC", "IOC", "FOK", "GTX"]} '
    default_pair_info = json.loads(default_pair_info_str)

    def test_load_orders_best_case(self):
        file = io.StringIO("BTCUSDT	26078	1	0	1	0	1	0	1	0	26900.1	0.003	0.00%")
        orders = main.load_orders(file)
        self.assertEqual(len(orders), 1)

    def test_load_orders_can_handle_empty_line(self):
        file = io.StringIO("BTCUSDT	26078	1	0	1	0	1	0	1	0	26900.1	0.003	0.00%\n\n")
        orders = main.load_orders(file)
        self.assertEqual(len(orders), 1)

    def test_standardize_price(self):
        price = main.standardize_precision('26900.187654', 2)
        self.assertEqual('26900.18', price)

    def test_standardize_precision_nothing(self):
        price = main.standardize_precision('26900.1', 2)
        self.assertEqual('26900.1', price)

    def test_standardize_precision_4(self):
        price = main.standardize_precision('26900.187654', 4)
        self.assertEqual('26900.1876', price)

    def test_standardize_precision_0(self):
        price = main.standardize_precision('26900.187654', 0)
        self.assertEqual('26900', price)

    def test_standardize_vol_lesser_than_min(self):
        vol = main.standardize_vol('0.5', self.default_pair_info)
        self.assertEqual('1', vol)

    def test_standardize_vol_larger_than_max(self):
        vol = main.standardize_vol('10000000', self.default_pair_info)
        self.assertEqual('5000', vol)

    def test_standardize_vol_precision(self):
        vol = main.standardize_vol('15.2345', self.default_pair_info)
        self.assertEqual('15', vol)

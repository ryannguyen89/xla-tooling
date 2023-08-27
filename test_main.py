from unittest import TestCase
import main
import io


class Test(TestCase):
    def test_load_orders_best_case(self):
        file = io.StringIO("BTCUSDT	26078	1	0	1	0	1	0	1	0	26900.1	0.003	0.00%")
        orders = main.load_orders(file)
        self.assertEqual(len(orders), 1)

    def test_load_orders_can_handle_empty_line(self):
        file = io.StringIO("BTCUSDT	26078	1	0	1	0	1	0	1	0	26900.1	0.003	0.00%\n\n")
        orders = main.load_orders(file)
        self.assertEqual(len(orders), 1)

    def test_standardize_price(self):
        price = main.standardize_price('26900.187654', 2)
        self.assertEqual('26900.18', price)

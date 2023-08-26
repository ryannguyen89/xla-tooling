import json
import logging
from binance.um_futures import UMFutures
from binance.lib.utils import config_logging
from binance.error import ClientError

DEFAULT_RECV_WINDOW = 15000

ORDER_SIDE_BUY = "BUY"
ORDER_SIDE_SELL = "SELL"

POSITION_SIZE_LONG = "LONG"
POSITION_SIZE_SHORT = "SHORT"

ORDER_TYPE_STM = "STOP_MARKET"
ORDER_TYPE_TS = "TRAILING_STOP_MARKET"


class Order:
    def __init__(self, symbol, is_open, is_long, is_stm, price, size, cbr, raw_req):
        self.raw_req = raw_req
        self.cbr = cbr
        self.size = size
        self.price = price
        self.is_stm = is_stm
        self.is_long = is_long
        self.symbol = symbol
        self.is_open = is_open

    def __str__(self):
        return f"Order info: {self.raw_req}"


def load_config():
    # Open config file
    f = open("config.json", "r")

    # returns JSON object as a dictionary
    c = json.load(f)

    # Close file
    f.close()

    return c


def load_orders():
    # Open config file
    f = open("orders.txt", "r")

    orders = []

    for line in f:
        items = line.split("\t")

        # handle open/close order
        if items[4] == '1' and items[5] == '0':
            is_open = True
        elif items[4] == '0' and items[5] == '1':
            is_open = False
        else:
            print("Error status at line: " + line)
            break

        # handle long/short order
        if items[6] == '1' and items[7] == '0':
            is_long = True
        elif items[6] == '0' and items[7] == '1':
            is_long = False
        else:
            print("Error type long/short at line: " + line)
            print("Type long:" + items[6])
            print("Type short:" + items[7])
            break

        # handle ts/stm order
        if items[8] == '1' and items[9] == "0":
            is_stm = True
        elif items[8] == "0" and items[9] == "1":
            is_stm = False
        else:
            print("Error order type at line: " + line)
            print("Order type STM:", items[8])
            print("Order type TS:", items[9])
            break
        print(items)
        cbr = float(items[12].strip("%\n"))
        if cbr == 0 and is_stm is False:
            print("TS order need CBR: " + line)
            break

        orders.append(Order(items[0], is_open, is_long, is_stm, items[10], items[11], cbr, line.strip("\n")))

    # Close file
    f.close()

    return orders


def send_orders(cli, orders):
    mark_price_dict = {}
    for order in orders:
        print("Sending order for: ", order.raw_req, "\n...")

        if order.symbol not in mark_price_dict:
            # get mark price
            mark_price = float(cli.mark_price(order.symbol)['markPrice'])
            mark_price_dict[order.symbol] = mark_price
            print("Mark price ", order.symbol, ": ", mark_price)
        else:
            mark_price = mark_price_dict.get(order.symbol)

        # order and position side
        trigger_price = float(order.price)
        if order.is_open:
            if order.is_long:
                if order.is_stm:
                    if trigger_price < mark_price:
                        txt = "Price {} must be larger than mark price {} to open order STM long"
                        print(txt.format(order.price, mark_price))
                        break
                else:
                    if trigger_price > mark_price:
                        txt = "Price {} must be lesser than mark price {} to open order TS long"
                        print(txt.format(order.price, mark_price))
                        break
                order_side = ORDER_SIDE_BUY
                position_side = POSITION_SIZE_LONG
            else:
                if order.is_stm:
                    if trigger_price > mark_price:
                        txt = "Price {} must be lesser than mark price {} to open order STM short"
                        print(txt.format(order.price, mark_price))
                        break
                else:
                    if trigger_price < mark_price:
                        txt = "Price {} must be larger than mark price {} to open order TS short"
                        print(txt.format(order.price, mark_price))
                        break
                order_side = ORDER_SIDE_SELL
                position_side = POSITION_SIZE_SHORT
        else:
            if order.is_long:
                if order.is_stm:
                    if trigger_price > mark_price:
                        txt = "Price {} must be lesser than mark price {} to close STM long"
                        print(txt.format(order.price, mark_price))
                        break
                else:
                    if trigger_price < mark_price:
                        txt = "Price {} must be lesser than mark price {} to close TS long"
                        print(txt.format(order.price, mark_price))
                        break
                order_side = ORDER_SIDE_SELL
                position_side = POSITION_SIZE_LONG
            else:
                if order.is_stm:
                    if trigger_price < mark_price:
                        txt = "Price {} must be larger than mark price {} to close STM short"
                        print(txt.format(order.price, mark_price))
                        break
                else:
                    if trigger_price > mark_price:
                        txt = "Price {} must be lesser than mark price {} to close TS short"
                        print(txt.format(order.price, mark_price))
                        break
                order_side = ORDER_SIDE_BUY
                position_side = POSITION_SIZE_SHORT

        # order type
        if order.is_stm:
            response = cli.new_order(
                symbol=order.symbol,
                side=order_side,
                positionSide=position_side,
                type=ORDER_TYPE_STM,
                quantity=order.size,
                timeInForce="GTC",
                stopPrice=order.price,
                recvWindow=DEFAULT_RECV_WINDOW
            )
        else:
            response = cli.new_order(
                symbol=order.symbol,
                side=order_side,
                positionSide=position_side,
                type=ORDER_TYPE_TS,
                quantity=order.size,
                timeInForce="GTC",
                activationPrice=order.price,
                callbackRate=order.cbr
            )
        logging.debug(response)
        print("Order sent successfully\n")


def send_stm_order(cli, order, mark_price):
    # order and position side
    trigger_price = float(order.price)
    if order.is_open:
        if order.is_long:
            if trigger_price < mark_price:
                txt = "Price {} must be larger than mark price {} to open STM long"
                print(txt.format(order.price, mark_price))
                return 1
            order_side = ORDER_SIDE_BUY
            position_side = POSITION_SIZE_LONG
        else:
            if trigger_price > mark_price:
                txt = "Price {} must be lesser than mark price {} to open STM short"
                print(txt.format(order.price, mark_price))
                return 1
            order_side = ORDER_SIDE_SELL
            position_side = POSITION_SIZE_SHORT
    else:
        if order.is_long:
            if trigger_price > mark_price:
                txt = "Price {} must be lesser than mark price {} to close STM long"
                print(txt.format(order.price, mark_price))
                return 1
            order_side = ORDER_SIDE_SELL
            position_side = POSITION_SIZE_LONG
        else:
            if trigger_price < mark_price:
                txt = "Price {} must be larger than mark price {} to close STM short"
                print(txt.format(order.price, mark_price))
                return 1
            order_side = ORDER_SIDE_BUY
            position_side = POSITION_SIZE_SHORT

    response = cli.new_order(
        symbol=order.symbol,
        side=order_side,
        positionSide=position_side,
        type=ORDER_TYPE_STM,
        quantity=order.size,
        timeInForce="GTC",
        stopPrice=order.price,
        recvWindow=DEFAULT_RECV_WINDOW
    )
    logging.debug(response)


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    # Load config
    config = load_config()
    api_key = config["api_key"]
    secret_key = config["secret_key"]

    config_logging(logging, logging.INFO)
    um_futures_client = UMFutures(key=api_key, secret=secret_key)

    list_orders = load_orders()

    try:
        # Get account information
        account_info = um_futures_client.account(recvWindow=DEFAULT_RECV_WINDOW)
        account_info_txt = "Your account info:\nWalletBalance: {}\nUnrealizedPnL: {}"
        print(account_info_txt.format(account_info["totalWalletBalance"], account_info["totalUnrealizedProfit"]))

        send_orders(um_futures_client, list_orders)
    except ClientError as error:
        logging.error(
            "Found error. status: {}, error code: {}, error message: {}".format(
                error.status_code, error.error_code, error.error_message
            )
        )

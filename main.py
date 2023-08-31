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
ORDER_TYPE_TAKE_PROFIT_MARKET = "TAKE_PROFIT_MARKET"

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
    file = open("config.json", "r")

    # returns JSON object as a dictionary
    c = json.load(file)

    # Close file
    file.close()

    return c


def load_orders(file):
    orders = []

    for line in file:
        items = line.split("\t")
        if len(items) != 13:
            print("Skip line:", line)
            continue

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

    return orders


def standardize_precision(value: str, precision: int) -> str:
    items = value.split(".")
    if len(items) == 1:
        return value

    if len(items[1]) > precision:
        if precision <= 0:
            return items[0]
        else:
            return ".".join([items[0], items[1][0:precision]])

    return value


def get_market_lot_size(pair_info: dict) -> dict:
    for item in pair_info["filters"]:
        if item["filterType"] == "MARKET_LOT_SIZE":
            return item

    return {}


def standardize_vol(vol: str, pair_info: dict) -> str:
    vol = standardize_precision(vol, pair_info["quantityPrecision"])
    market_lot_size = get_market_lot_size(pair_info)
    min_qty = market_lot_size["minQty"]
    max_qty = market_lot_size["maxQty"]

    if float(vol) < float(min_qty):
        return min_qty

    if float(vol) > float(max_qty):
        return max_qty

    return vol


def send_orders(cli, orders, exchange_info_dict):
    mark_price_dict = {}
    for order in orders:
        print("Sending order for:", order.raw_req, "\n...")

        # Prepare mark price
        if order.symbol not in mark_price_dict:
            # get mark price
            mark_price = float(cli.mark_price(order.symbol)['markPrice'])
            mark_price_dict[order.symbol] = mark_price
            print("Mark price", order.symbol, ": ", mark_price)
        else:
            mark_price = mark_price_dict.get(order.symbol)

        # order and position side
        trigger_price = float(order.price)
        order_type = ORDER_TYPE_STM
        if order.is_open:
            if order.is_long:
                if order.is_stm:
                    if trigger_price < mark_price:
                        order_type = ORDER_TYPE_TAKE_PROFIT_MARKET
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
                        order_type = ORDER_TYPE_TAKE_PROFIT_MARKET
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
                        order_type = ORDER_TYPE_TAKE_PROFIT_MARKET
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
                        order_type = ORDER_TYPE_TAKE_PROFIT_MARKET
                else:
                    if trigger_price > mark_price:
                        txt = "Price {} must be lesser than mark price {} to close TS short"
                        print(txt.format(order.price, mark_price))
                        break
                order_side = ORDER_SIDE_BUY
                position_side = POSITION_SIZE_SHORT

        # Prepare pair info
        pair_info = exchange_info_dict[order.symbol]

        # standardize trigger price
        trigger_price_str = standardize_precision(order.price, pair_info["pricePrecision"])

        # standardize vol
        vol = standardize_vol(str(order.size), pair_info)

        # order type
        if order.is_stm:
            print("OrderType:", order_type)
            response = cli.new_order(
                symbol=order.symbol,
                side=order_side,
                positionSide=position_side,
                type=order_type,
                quantity=vol,
                timeInForce="GTC",
                stopPrice=trigger_price_str,
                recvWindow=DEFAULT_RECV_WINDOW
            )
        else:
            print("OrderType:", ORDER_TYPE_TS)
            response = cli.new_order(
                symbol=order.symbol,
                side=order_side,
                positionSide=position_side,
                type=ORDER_TYPE_TS,
                quantity=vol,
                timeInForce="GTC",
                activationPrice=trigger_price_str,
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


def load_exchange_info(response):
    exchange_info_dict = {}
    for symbol in response["symbols"]:
        exchange_info_dict[symbol["symbol"]] = symbol

    return exchange_info_dict


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    print("Initializing...")
    # Load config
    config = load_config()
    api_key = config["api_key"]
    secret_key = config["secret_key"]

    config_logging(logging, logging.INFO)
    um_futures_client = UMFutures(key=api_key, secret=secret_key)

    # Load orders
    f = open("orders.txt", "r")
    list_orders = load_orders(f)
    f.close()
    print("Load orders successfully!")

    try:
        # Get account information
        account_info = um_futures_client.account(recvWindow=DEFAULT_RECV_WINDOW)
        account_info_txt = "Your account info:\nWalletBalance: {}\nUnrealizedPnL: {}"
        print(account_info_txt.format(account_info["totalWalletBalance"], account_info["totalUnrealizedProfit"]))

        exchange_info_response = um_futures_client.exchange_info()
        exchange_info = load_exchange_info(exchange_info_response)

        print("Start sending orders...")
        send_orders(um_futures_client, list_orders, exchange_info)
    except ClientError as error:
        logging.error(
            "Found error. status: {}, error code: {}, error message: {}".format(
                error.status_code, error.error_code, error.error_message
            )
        )

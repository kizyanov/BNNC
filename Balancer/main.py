"""Bnnc Balancer."""

import asyncio
from decimal import Decimal

import orjson
from decouple import Csv, config
from loguru import logger
from nats.js import JetStreamContext
from websockets import ClientProtocol, connect

from models import Access, OrderBook, Token
from natslocal import get_js_context
from tools import (
    exchangeinfo,
    get_margin_account,
    get_websocket_listen_key,
    keep_alive_listen_key,
)


async def fill_base_increment(orderbook: OrderBook) -> None:

    # Get exchangeinfo about tickSize
    symbol_info = await exchangeinfo(list(orderbook.order_book))

    for symbol in symbol_info["symbols"]:

        step = [
            filter_symbol
            for filter_symbol in symbol["filters"]
            if filter_symbol["filterType"] == "LOT_SIZE"
        ][0]["stepSize"]

        orderbook.fill_base_increment_by_symbol(
            symbol["symbol"],
            step[: step.index("1") + 1],  # 0.010000000 to 0.01
        )


async def fill_base_available(access: Access, orderbook: OrderBook) -> None:

    # Get all assert for margin trade
    account_data = await get_margin_account(access)

    for asset in account_data["userAssets"]:
        custom_asset = f"{asset['asset']}USDT"

        # filter only asset in order_book
        if custom_asset in orderbook.order_book:
            orderbook.fill_base_available_by_symbol(custom_asset, asset["free"])


async def init_order_book(
    access: Access,
    orderbook: OrderBook,
) -> None:
    """First init order_book."""
    # fill base increment by symbol from orderbook
    await fill_base_increment(orderbook)
    await fill_base_available(access, orderbook)


async def run_keep_alive(access: Access, listenKey: str) -> None:
    while True:
        await keep_alive_listen_key(access, listenKey)
        await asyncio.sleep(600)  # sleep 10 min


async def balance(
    msg: dict,
    orderbook: OrderBook,
    js: JetStreamContext,
) -> None:
    """Work with change amount of balance on exchange."""
    logger.info(msg)

    if msg["e"] == "outboundAccountPosition":
        # {'e': 'outboundAccountPosition', 'E': 1733347691452, 'u': 1733347691452, 'B': [{'a': 'USDT', 'f': '2000.07982380', 'l': '0.00000000'}]}
        for symbol in msg["B"]:
            logger.info(symbol)
            if symbol["a"] != "USDT":

                # token name + symbol['a']  BTCUSDT
                symbol_ = f"{symbol['a']}USDT"

                await js.publish(
                    "balance",
                    orjson.dumps(
                        {
                            "symbol": symbol_,
                            "baseincrement": orderbook.order_book[symbol_][
                                "baseincrement"
                            ],
                            "available": symbol["f"],
                        },
                    ),
                )
                orderbook.order_book[symbol_]["available"] = symbol["f"]

                logger.success(f"Success sent:{symbol_}:{ symbol['f']}")


async def web_socket(listen_key: str, orderbook: OrderBook, js: JetStreamContext):
    async with connect(
        uri=f"wss://stream.binance.com:443/ws/{listen_key}",
        max_queue=1024,
    ) as ws:

        background_tasks = set()

        while True:
            msg = await ws.recv()

            task = asyncio.create_task(
                balance(
                    orjson.loads(msg),
                    orderbook,
                    js,
                ),
            )
            background_tasks.add(task)
            task.add_done_callback(background_tasks.discard)


async def main() -> None:
    """Main func in microservice."""
    logger.info("Start Balancer")

    # Access object
    access = Access(
        key=config("KEY", cast=str),
        secret=config("SECRET", cast=str),
        base_uri="https://api.binance.com",
    )

    # Token's object
    token = Token(
        currency=config("ALLCURRENCY", cast=Csv(str)),
        ignore_currency=config("IGNORECURRENCY", cast=Csv(str)),
        base_keep=Decimal(config("BASE_KEEP", cast=int)),
        time_shift=config("TIME_SHIFT", cast=str, default="1h"),
        base_stable=config("BASE_STABLE", cast=str, default="USDT"),
    )

    orderbook = OrderBook(token=token)

    await init_order_book(access, orderbook)

    js = await get_js_context()

    # Send first initial balance from excange
    await orderbook.send_balance(js)

    listen_key_resp = await get_websocket_listen_key(access)
    listen_key = listen_key_resp["listenKey"]

    async with asyncio.TaskGroup() as tg:
        tg.create_task(web_socket(listen_key, orderbook, js))
        tg.create_task(run_keep_alive(access, listen_key))

    await asyncio.sleep(60 * 60 * 24 * 365)  # Wait 1 year


if __name__ == "__main__":
    asyncio.run(main())

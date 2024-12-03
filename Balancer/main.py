"""Bnnc Balancer."""

import asyncio
from decimal import Decimal

from decouple import Csv, config
from loguru import logger

from models import Access, OrderBook, Token
from natslocal import get_js_context
from tools import get_margin_account


async def init_order_book(
    access: Access,
    orderbook: OrderBook,
) -> None:
    """First init order_book."""
    account_data = await get_margin_account(access)
    logger.info(account_data)


async def main() -> None:
    """Main func in microservice."""
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
    # await orderbook.send_balance(js)

    await asyncio.sleep(60 * 60 * 24 * 365)


if __name__ == "__main__":
    asyncio.run(main())

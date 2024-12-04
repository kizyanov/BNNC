"""Bnnc Orderest."""

import asyncio

from decouple import config
from loguru import logger

from models import Access
from tools import cancel_order, get_order_list, get_seconds_to_next_minutes


async def find_order_for_cancel(access: Access) -> None:
    """Find order created more then 1 hour ago."""
    orders = await get_order_list(access)
    logger.info(orders)
    for order in orders:
        logger.warning(f"Need cancel:{order['symbol']}:{order['orderId']}")
        # need more info about DELETE method
        await cancel_order(access, order["symbol"], order["orderId"])


async def main() -> None:
    """Main func in microservice."""
    logger.info("Run Orderest microservice")

    # Access object
    access = Access(
        key=config("KEY", cast=str),
        secret=config("SECRET", cast=str),
        base_uri="https://api.binance.com",
    )

    await find_order_for_cancel(access)

    while True:
        wait_seconds = get_seconds_to_next_minutes(58)

        logger.info(f"Wait {wait_seconds} to run find_order_for_cancel")
        await asyncio.sleep(wait_seconds)

        await find_order_for_cancel(access)


if __name__ == "__main__":
    asyncio.run(main())

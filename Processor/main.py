"""Bnnc Processor."""

import asyncio
from decimal import Decimal

import orjson
from decouple import Csv, config
from loguru import logger
from nats.aio.client import Msg

from models import Access, Token
from natslocal import get_js_context


async def candle(msg: Msg) -> None:
    """Collect data of open price each candle by interval."""
    logger.debug(msg.data.decode())
    # symbol, price_str = orjson.loads(msg.data).popitem()

    await msg.ack()


async def main() -> None:
    """Main func in microservice."""
    logger.info("Start Processor")

    js = await get_js_context()

    # Access object
    access = Access(
        key=config("KEY", cast=str),
        secret=config("SECRET", cast=str),
        base_uri="https://api.binance.com",
    )
    # Token's object
    token = Token(
        time_shift=config("TIME_SHIFT", cast=str, default="1h"),
        base_stable=config("BASE_STABLE", cast=str, default="USDT"),
        currency=config("ALLCURRENCY", cast=Csv(str)),
        ignore_currency=config("IGNORECURRENCY", cast=Csv(str)),
        base_keep=Decimal(config("BASE_KEEP", cast=int)),
    )

    await js.add_stream(name="bnnc", subjects=["candle", "balance"])

    await js.subscribe("candle", "candle", cb=candle)

    await asyncio.sleep(60 * 60 * 24 * 365)


if __name__ == "__main__":
    asyncio.run(main())

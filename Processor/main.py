"""Bnnc Processor."""

import asyncio

from decouple import config
from loguru import logger

from models import Access
from natslocal import get_js_context


async def main() -> None:
    """Main func in microservice."""
    # Access object
    access = Access(
        key=config("KEY", cast=str),
        secret=config("SECRET", cast=str),
        base_uri="https://api.binance.com",
    )
    logger.info(access)

    await asyncio.sleep(60 * 60 * 24 * 365)

    js = await get_js_context()
    await js.add_stream(name="bnnc", subjects=["candle", "balance"])


if __name__ == "__main__":
    asyncio.run(main())

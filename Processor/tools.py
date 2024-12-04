"""Tools for Alertest."""

from time import time

import aiohttp
from loguru import logger

from models import Access


async def get_margin_account(access: Access) -> dict:
    """Get margin account user data."""
    logger.info("Run get_margin_account")

    timestamp = int(time() * 1000)

    data = {"recvWindows": 10000, "timestamp": timestamp}

    query_string = "&".join([f"{k}={v}" for k, v in data.items()])

    signature = access.encrypted(query_string)
    data.update({"signature": signature})

    async with (
        aiohttp.ClientSession(
            headers={"X-MBX-APIKEY": access.key},
        ) as session,
        session.get(
            url=f"https://api.binance.com/sapi/v1/margin/account",
            params=data,
        ) as resp,
    ):
        return await resp.json()


async def exchangeinfo(tokens: list[str]) -> dict:
    """Get ExcangeInfo about tickSize.

    https://api.binance.com/api/v3/exchangeInfo?symbols=["ADAUSDT","BTCUSDT"]
    """
    logger.info("Run exchangeinfo")

    filter_tokens = str(tokens).replace(" ", "").replace("'", '"')

    url = "https://api.binance.com/api/v3/exchangeInfo"

    async with (
        aiohttp.ClientSession() as session,
        session.get(
            url=url,
            params={
                "symbols": filter_tokens,
            },
        ) as resp,
    ):
        return await resp.json()


async def make_margin_limit_order(
    access: Access,
    side: str,
    price: str,
    symbol: str,
    size: str,
) -> dict:
    """Make limit order by price."""
    logger.info(f"Run make_margin_limit_order:{side}:{symbol}")

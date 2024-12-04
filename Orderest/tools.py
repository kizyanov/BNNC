"""Tools for Orderest."""

from datetime import UTC, datetime
from time import time

import aiohttp
from loguru import logger
from orjson import loads

from models import Access


async def request(
    url: str,
    method: str,
    headers: dict,
    *,
    data_json: str | None = None,
) -> dict:
    """Universal http reqponse."""
    async with (
        aiohttp.ClientSession(headers=headers) as session,
        session.request(method, url, data=data_json) as response,
    ):
        res = await response.read()  # bytes
        data = loads(res)  # dict ['code':str, 'data':dict]

        match data["code"]:
            case "200000":
                result = data["data"]
                logger.success(f"{response.status}:{method}:{url}")
            case _:
                logger.warning(f"{response.status}:{method}:{url}:{headers}")
                result = {}

        return result


async def cancel_order(access: Access, symbol: str, order_id: int) -> None:
    """Cancel order by number."""
    logger.info("Run cancel_order")

    timestamp = int(time() * 1000)

    data = {
        "recvWindows": 10000,
        "timestamp": timestamp,
        "symbol": symbol,
        "orderId": order_id,
    }

    query_string = "&".join([f"{k}={v}" for k, v in data.items()])

    signature = access.encrypted(query_string)
    data.update({"signature": signature})

    async with (
        aiohttp.ClientSession(
            headers={
                "X-MBX-APIKEY": access.key,
                "Content-Type": "application/x-www-form-urlencoded",
            },
        ) as session,
        session.delete(
            url=f"https://api.binance.com/sapi/v1/margin/order",
            params=data,
        ) as resp,
    ):
        return await resp.json()


async def get_order_list(access: Access) -> dict:
    """Get all active orders in excange."""
    logger.info("Run get_order_list")

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
            url=f"https://api.binance.com/sapi/v1/margin/openOrders",
            params=data,
        ) as resp,
    ):
        return await resp.json()


def get_seconds_to_next_minutes(minutes: int) -> int:
    """Get next 10:00 minutes."""
    logger.info("Run get_seconds_to_next_minutes")

    now = datetime.now(tz=UTC)

    if now.minute > minutes:
        result_minute = 60 - now.minute + minutes
    elif now.minute < minutes:
        result_minute = minutes - now.minute
    else:
        result_minute = minutes

    return result_minute * 60

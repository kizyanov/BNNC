"""Tools for Alertest."""

from datetime import UTC, datetime
from time import time

import aiohttp
from loguru import logger
from orjson import loads

from models import Access


def get_data_json(params: dict) -> str:
    """Convert dict to url params."""
    data_json = ""

    data_json += "&".join([f"{key}={params[key]}" for key in sorted(params)])
    return data_json


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


async def get_margin_account(access: Access) -> dict:
    """Get margin account user data."""
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
            url="https://api.binance.com/sapi/v1/margin/account",
            params=data,
        ) as resp,
    ):
        return await resp.json()


async def exchangeinfo(tokens: list[str]) -> dict:
    """Get ExcangeInfo about tickSize.

    https://api.binance.com/api/v3/exchangeInfo?symbols=["ADAUSDT","BTCUSDT"]
    """
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


def get_seconds_to_next_minutes(minutes: int) -> int:
    """Get next 10:00 minutes."""
    now = datetime.now(tz=UTC)

    if now.minute >= minutes:
        result_minute = 60 - now.minute + minutes
    else:
        result_minute = minutes - now.minute

    return result_minute * 60


async def get_websocket_listen_key(access: Access) -> dict:
    """Get listenKey for websocket.

    {
            "listenKey": "..."
    }
    """
    async with (
        aiohttp.ClientSession(
            headers={
                "X-MBX-APIKEY": access.key,
            },
        ) as session,
        session.post(
            url="https://api.binance.com/sapi/v1/userDataStream",
        ) as resp,
    ):
        return await resp.json()


async def keep_alive_listen_key(access: Access, listen_key: str) -> dict:
    """KeepAlive for listenKey."""
    params = {"listenKey": listen_key}
    async with (
        aiohttp.ClientSession(
            headers={
                "X-MBX-APIKEY": access.key,
            },
        ) as session,
        session.put(
            url="https://api.binance.com/sapi/v1/userDataStream",
            params=params,
        ) as resp,
    ):
        return await resp.json()

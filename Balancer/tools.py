"""Tools for Alertest."""

import hashlib
import hmac
from datetime import UTC, datetime
from time import time
from urllib.parse import urljoin

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


def hmac_signature(access: Access, query_string: str) -> str:
    """Get hmac sign msg."""
    return hmac.new(
        access.secret.encode(),
        query_string.encode(),
        hashlib.sha256,
    ).hexdigest()


async def get_margin_account(access: Access) -> dict:
    """Get margin account user data."""
    logger.info("Run get_margin_account")

    timestamp = int(time() * 1000)

    data = {"recvWindows": 10000, "timestamp": timestamp}

    query_string = "&".join([f"{k}={v}" for k, v in data.items()])

    signature = hmac_signature(access, query_string)
    data.update({"signature": signature})

    d = "&".join(f"{k}={v}" for k, v in data.items())

    async with aiohttp.ClientSession(headers={"X-MBX-APIKEY": access.key}) as session:
        async with session.get(
            url=f"https://api.binance.com/sapi/v1/margin/account?{d}",
        ) as resp:
            return await resp.json()


def get_seconds_to_next_minutes(minutes: int) -> int:
    """Get next 10:00 minutes."""
    logger.info("Run get_seconds_to_next_minutes")

    now = datetime.now(tz=UTC)

    if now.minute >= minutes:
        result_minute = 60 - now.minute + minutes
    else:
        result_minute = minutes - now.minute

    return result_minute * 60

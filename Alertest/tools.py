"""Tools for Alertest."""

import hashlib
import hmac
from datetime import UTC, datetime
from time import time
from urllib.parse import urljoin

import aiohttp
from loguru import logger
from orjson import loads

from models import Access, Telegram


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


def get_headers(
    access: Access = None,
    str_to_sign: str = "",
    now_time: str = "",
    *,
    auth: bool = True,
) -> dict:
    """Get headers for request."""
    if auth:
        result = {
            "KC-API-SIGN": access.encrypted(str_to_sign),
            "KC-API-TIMESTAMP": now_time,
            "KC-API-PASSPHRASE": access.encrypted(access.passphrase),
            "KC-API-KEY": access.key,
            "Content-Type": "application/json",
            "KC-API-KEY-VERSION": "2",
            "User-Agent": "kucoin-python-sdk/2",
        }
    else:
        result = {
            "User-Agent": "kucoin-python-sdk/2",
        }

    return result


async def get_symbol_list(
    access: Access,
    *,
    method: str = "GET",
    uri: str = "/api/v2/symbols",
) -> dict:
    """Get all tokens in excange."""
    logger.info("Run get_symbol_list")
    return await request(
        urljoin(access.base_uri, uri),
        method,
        get_headers(auth=False),
    )


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

    logger.info(query_string)

    signature = hmac_signature(access, query_string)
    data.update({"signature": signature})

    d = "&".join(f"{k}={v}" for k, v in data.items())

    async with aiohttp.ClientSession(headers={"X-MBX-APIKEY": access.key}) as session:
        async with session.get(
            url=f"https://api.binance.com/sapi/v1/margin/account?{d}",
        ) as resp:
            return await resp.json()


async def send_telegram_msg(telegram: Telegram, text: str) -> None:
    """Send msg to telegram."""
    for chat_id in telegram.get_bot_chat_id():
        async with (
            aiohttp.ClientSession() as session,
            session.post(
                telegram.get_telegram_url(),
                json={
                    "chat_id": chat_id,
                    "parse_mode": "HTML",
                    "disable_notification": True,
                    "text": text,
                },
            ),
        ):
            pass


def get_seconds_to_next_minutes(minutes: int) -> int:
    """Get next 10:00 minutes."""
    logger.info("Run get_seconds_to_next_minutes")

    now = datetime.now(tz=UTC)

    if now.minute >= minutes:
        result_minute = 60 - now.minute + minutes
    else:
        result_minute = minutes - now.minute

    return result_minute * 60


async def get_filled_order_list(
    access: Access,
    params: dict,
    *,
    method: str = "GET",
    uri: str = "/api/v1/orders",
) -> dict:
    """Get all active orders in excange."""
    logger.info("Run get_order_list")

    uri += "?" + get_data_json(params)
    now_time = str(int(time()) * 1000)

    return await request(
        urljoin(access.base_uri, uri),
        method,
        get_headers(
            access,
            f"{now_time}{method}{uri}",
            now_time,
        ),
    )


async def get_server_timestamp(
    access: Access,
    *,
    uri: str = "/api/v1/timestamp",
    method: str = "GET",
) -> dict:
    """Get timestamp from excange server."""
    logger.info("Run get_server_timestamp")

    now_time = str(int(time()) * 1000)

    return await request(
        urljoin(access.base_uri, uri),
        method,
        get_headers(
            access,
            f"{now_time}{method}{uri}",
            now_time,
        ),
    )

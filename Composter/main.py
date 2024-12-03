"""bnnc_composeter."""

import asyncio
from decimal import Decimal

import orjson
from decouple import Csv, config
from loguru import logger
from nats.js import JetStreamContext
from websockets import connect

from models import Token
from natslocal import get_js_context


async def main() -> None:
    """Main func in microservice."""
    js = await get_js_context()

    # Token's object
    token = Token(
        time_shift=config("TIME_SHIFT", cast=str, default="1h"),
        base_stable=config("BASE_STABLE", cast=str, default="USDT"),
        currency=config("ALLCURRENCY", cast=Csv(str)),
        ignore_currency=config("IGNORECURRENCY", cast=Csv(str)),
        base_keep=Decimal(config("BASE_KEEP", cast=int)),
    )

    async def candle(msg: dict, js: JetStreamContext, token: Token) -> None:
        symbol = msg["s"]
        open_price = msg["o"]

        # Need BTC-USDT format
        logger.info(f"candle: {symbol}:{open_price} {msg}")

        if token.history[symbol] != open_price:
            logger.info(f"{symbol}:{open_price}")
            token.history[symbol] = open_price

    token.init_history()

    async with connect(
        uri=token.get_url_websocket(),
        max_queue=1024,
    ) as ws:
        background_tasks = set()

        while True:
            recv = await ws.recv()

            task = asyncio.create_task(
                candle(
                    orjson.loads(recv)["data"]["k"],
                    js,
                    token,
                ),
            )
            background_tasks.add(task)
            task.add_done_callback(background_tasks.discard)


if __name__ == "__main__":
    asyncio.run(main())

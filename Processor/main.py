"""Bnnc Processor."""

import asyncio
from decimal import ROUND_DOWN, Decimal

import orjson
from decouple import Csv, config
from loguru import logger
from nats.aio.client import Msg

from models import Access, Token
from natslocal import get_js_context
from tools import make_margin_limit_order


def get_side_and_size(
    available: Decimal,
    baseincrement: Decimal,
    price: Decimal,
    token: Token,
) -> dict:
    """Get side of trade and size of tokens."""
    # Get new balance by new price and available count of token's
    # Decimal type
    new_balance = price * available

    # default "0" count of token's
    tokens_count = Decimal("0")

    if new_balance >= token.base_keep:
        # need sell of part
        tokens_count = (new_balance - token.base_keep) / price
        side = "sell"

    else:
        # need buy of part
        tokens_count = (token.base_keep - new_balance) / price
        side = "buy"

    # Round by increment token
    size = tokens_count.quantize(
        baseincrement,
        ROUND_DOWN,
    )

    return {"side": side, "size": size}


async def candle(msg: Msg) -> None:
    """Collect data of open price each candle by interval.

    recieve in format
    {"TRXUSDT": "0.38640000"}
    """
    data = orjson.loads(msg.data)
    logger.info(data)

    for symbol, price in data.items():
        logger.info(symbol, price)

        # check if token not yet send balance
        if symbol in ledger:

            # get side and size
            sidze = get_side_and_size(
                ledger[symbol]["available"],
                ledger[symbol]["baseincrement"],
                Decimal(price),
                token,
            )

            if sidze["size"] != Decimal("0.0"):  # check on buy '0' count of tokens
                logger.warning(sidze)

                # make limit order
                await make_margin_limit_order(
                    access=access,
                    side=sidze["side"],
                    price=price,
                    symbol=symbol,
                    size=sidze["size"],
                )

    await msg.ack()


async def balance(msg: Msg) -> None:
    """Collect balance of each tokens.

    recieve in format
    {"symbol": "TRXUSDT", "baseincrement": "0.00010000", "available": "0"}
    """
    data = orjson.loads(msg.data)

    symbol = data["symbol"]
    available = data["available"]
    baseincrement = data["baseincrement"]

    ledger.update(
        {
            symbol: {
                "baseincrement": Decimal(baseincrement),
                "available": Decimal(available),
            },
        },
    )

    logger.success(f"Change balance:{symbol} to {available}")

    await msg.ack()


async def main() -> None:
    """Main func in microservice."""
    logger.info("Start Processor")
    global ledger, access, token
    ledger = {}

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
    await js.subscribe("balance", "balance", cb=balance)

    await asyncio.sleep(60 * 60 * 24 * 365)  # Wait 1 year


if __name__ == "__main__":
    asyncio.run(main())

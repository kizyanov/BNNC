import asyncio
from nats.aio.client import Client
import orjson
import uvloop
from loguru import logger
from decouple import config, Csv

key = config("KEY", cast=str)
secret = config("SECRET", cast=str)
passphrase = config("PASSPHRASE", cast=str)
all_currency = config("ALLCURRENCY", cast=Csv(str))  # Tokens for trade in bot



async def main():
    pass

    await asyncio.sleep(60 * 60 * 24 * 365)


if __name__ == "__main__":
    with asyncio.Runner(loop_factory=uvloop.new_event_loop) as runner:
        runner.run(main())

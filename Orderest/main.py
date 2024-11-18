import asyncio
import uvloop
from decouple import config
from base64 import b64encode
from loguru import logger
import hmac
import hashlib
import time
from urllib.parse import urljoin
import aiohttp


key = config("KEY", cast=str)
secret = config("SECRET", cast=str)
passphrase = config("PASSPHRASE", cast=str)

async def main() -> None:
    pass

if __name__ == "__main__":
    with asyncio.Runner(loop_factory=uvloop.new_event_loop) as runner:
        runner.run(main())

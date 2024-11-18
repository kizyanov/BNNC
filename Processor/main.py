import asyncio
from uuid import uuid4
import random
from nats.aio.client import Client
import uvloop
from json import loads, dumps
from decouple import config, Csv
from base64 import b64encode
from loguru import logger
from decimal import Decimal, ROUND_DOWN
import hmac
import hashlib
import time
from urllib.parse import urljoin
from uuid import uuid1
import aiohttp
from natslocal import get_js_context
from models import Access, Token

key = config("KEY", cast=str)
secret = config("SECRET", cast=str).encode("utf-8")
passphrase = config("PASSPHRASE", cast=str)
base_keep = Decimal(config("BASE_KEEP", cast=int))



async def main() -> None:
    """Main func in microservice."""
    pass


if __name__ == "__main__":
    with asyncio.Runner(loop_factory=uvloop.new_event_loop) as runner:
        runner.run(main())

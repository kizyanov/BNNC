"""Bnnc Balancer."""
import asyncio
from decouple import config, Csv

key = config("KEY", cast=str)
secret = config("SECRET", cast=str)
passphrase = config("PASSPHRASE", cast=str)
all_currency = config("ALLCURRENCY", cast=Csv(str))  # Tokens for trade in bot


async def main():
    pass

    await asyncio.sleep(60 * 60 * 24 * 365)


if __name__ == "__main__":
    asyncio.run(main())

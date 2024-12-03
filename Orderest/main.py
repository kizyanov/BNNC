"""Bnnc Orderest."""

import asyncio

from decouple import config

key = config("KEY", cast=str)
secret = config("SECRET", cast=str)


async def main() -> None:
    """Main func in microservice."""
    await asyncio.sleep(60 * 60 * 24 * 365)


if __name__ == "__main__":
    asyncio.run(main())

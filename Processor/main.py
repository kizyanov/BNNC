import asyncio
from decouple import config
from decimal import Decimal

key = config("KEY", cast=str)
secret = config("SECRET", cast=str).encode("utf-8")
passphrase = config("PASSPHRASE", cast=str)
base_keep = Decimal(config("BASE_KEEP", cast=int))


async def main() -> None:
    """Main func in microservice."""
    pass


if __name__ == "__main__":
    asyncio.run(main())

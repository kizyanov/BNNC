import asyncio
from decouple import config


key = config("KEY", cast=str)
secret = config("SECRET", cast=str)
passphrase = config("PASSPHRASE", cast=str)


async def main() -> None:
    pass


if __name__ == "__main__":
    asyncio.run(main())

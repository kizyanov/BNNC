"""Classes for work."""

import hashlib
import hmac
from base64 import b64encode
from decimal import Decimal
from typing import Self


class Access:
    """Class for store access condention to exchange."""

    def __init__(self, key: str, secret: str, base_uri: str) -> None:
        """Init access condention keys."""
        self.key: str = key
        self.secret: str = secret
        self.base_uri: str = base_uri

    def encrypted(self: Self, msg: str) -> str:
        """Encrypted msg for exchange."""
        return b64encode(
            hmac.new(
                self.secret.encode("utf-8"),
                msg.encode("utf-8"),
                hashlib.sha256,
            ).digest(),
        ).decode()

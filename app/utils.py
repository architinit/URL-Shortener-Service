import hashlib
import string
from datetime import datetime, timezone

ALPHABET = string.digits + string.ascii_lowercase + string.ascii_uppercase
BASE = len(ALPHABET)


def encode_base62(number: int) -> str:
    if number == 0:
        return ALPHABET[0]
    chars = []
    while number > 0:
        number, remainder = divmod(number, BASE)
        chars.append(ALPHABET[remainder])
    return "".join(reversed(chars))


def short_code_for_id(link_id: int, length: int = 6) -> str:
    return encode_base62(link_id).rjust(length, ALPHABET[0])


def hash_ip(ip: str) -> str:
    return hashlib.sha256(ip.encode()).hexdigest()[:16]


def utcnow() -> datetime:
    """Naive UTC datetime, matching the (now-deprecated) datetime.utcnow() semantics."""
    return datetime.now(timezone.utc).replace(tzinfo=None)

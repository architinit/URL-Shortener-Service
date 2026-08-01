import hashlib
import string

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


def generate_short_code(long_url: str, salt: str, length: int = 6) -> str:
    digest = hashlib.sha256(f"{long_url}{salt}".encode()).hexdigest()
    number = int(digest, 16)
    return encode_base62(number)[:length]


def hash_ip(ip: str) -> str:
    return hashlib.sha256(ip.encode()).hexdigest()[:16]

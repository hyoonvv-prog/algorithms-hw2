"""Base62 encoding using the digits, lowercase, and uppercase ASCII letters."""

ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
BASE = len(ALPHABET)


def encode(value: int) -> str:
    """Encode a non-negative integer as a base62 string."""
    if type(value) is not int:
        raise TypeError("value must be an integer")
    if value < 0:
        raise ValueError("value must be non-negative")
    if value == 0:
        return "0"

    encoded = []
    while value:
        value, remainder = divmod(value, BASE)
        encoded.append(ALPHABET[remainder])
    return "".join(reversed(encoded))


def decode(code: str) -> int:
    """Decode a base62 string into a non-negative integer."""
    if not isinstance(code, str):
        raise TypeError("code must be a string")
    if not code:
        raise ValueError("code must not be empty")

    value = 0
    for character in code:
        try:
            digit = ALPHABET.index(character)
        except ValueError as error:
            raise ValueError(f"invalid base62 character: {character!r}") from error
        value = value * BASE + digit
    return value

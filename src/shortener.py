"""In-memory URL shortener backed by the project's hash table."""

from urllib.parse import urlsplit

from src.base62 import encode
from src.hash_table import HashTable, LinearProbingHashTable


Table = HashTable[str] | LinearProbingHashTable[str]


class Shortener:
    def __init__(self, table_type: str = "chaining", capacity: int = 101) -> None:
        if table_type not in ("chaining", "linear"):
            raise ValueError("table_type must be 'chaining' or 'linear'")
        self.table_type = table_type
        self.capacity = capacity
        table_class = HashTable if table_type == "chaining" else LinearProbingHashTable
        self._url_to_code: Table = table_class(capacity)
        self._code_to_url: Table = table_class(capacity)
        self._next_id = 0

    @staticmethod
    def _normalize_url(url: str) -> str:
        if not isinstance(url, str):
            raise TypeError("url must be a string")
        normalized = url.strip()
        if not normalized or any(character.isspace() for character in normalized):
            raise ValueError("url must be a non-empty URL without whitespace")
        try:
            parts = urlsplit(normalized)
            hostname = parts.hostname
            parts.port
        except ValueError as error:
            raise ValueError("url must be a valid HTTP or HTTPS URL") from error
        if parts.scheme.lower() not in ("http", "https") or not hostname:
            raise ValueError("url must be a valid HTTP or HTTPS URL")

        scheme_end = normalized.find(":")
        authority_start = scheme_end + 3
        authority_end = len(normalized)
        for delimiter in "/?#":
            position = normalized.find(delimiter, authority_start)
            if position != -1 and position < authority_end:
                authority_end = position
        authority = normalized[authority_start:authority_end]
        userinfo, separator, host_port = authority.rpartition("@")
        host_start = len(userinfo) + len(separator)
        if host_port.startswith("["):
            host_end = authority_start + host_start + host_port.find("]") + 1
            host_start += 1
        else:
            colon = host_port.find(":")
            host_length = colon if colon != -1 else len(host_port)
            host_end = authority_start + host_start + host_length
        host = normalized[authority_start + host_start:host_end]
        return (
            normalized[:scheme_end].lower()
            + normalized[scheme_end:authority_start + host_start]
            + host.lower()
            + normalized[host_end:]
        )

    def shorten(self, url: str) -> str:
        normalized = self._normalize_url(url)
        found, _, _ = self._url_to_code.find(normalized)
        if found:
            return self._url_to_code.get(normalized)

        if len(self._url_to_code) >= self.capacity:
            raise OverflowError("shortener table is full")
        code = encode(self._next_id)
        self._url_to_code.set(normalized, code)
        self._code_to_url.set(code, normalized)
        self._next_id += 1
        return code

    def expand(self, code: str) -> str:
        return self._code_to_url.get(code)

    @property
    def table(self) -> Table:
        return self._url_to_code

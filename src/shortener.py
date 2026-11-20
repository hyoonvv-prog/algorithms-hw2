"""In-memory URL shortener backed by the project's hash table."""

from urllib.parse import urlsplit

from src.hash_table import HashTable
from src.base62 import encode


class Shortener:
    def __init__(self, table_type: str = "chaining", capacity: int = 101) -> None:
        if table_type != "chaining":
            raise ValueError("table_type must be 'chaining'")
        self.table_type = table_type
        self.capacity = capacity
        self._url_to_code: HashTable[str] = HashTable(capacity)
        self._code_to_url: HashTable[str] = HashTable(capacity)
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
        return normalized

    def shorten(self, url: str) -> str:
        normalized = self._normalize_url(url)
        found, _, _ = self._url_to_code.find(normalized)
        if found:
            return self._url_to_code.get(normalized)

        code = encode(self._next_id)
        self._next_id += 1
        self._url_to_code.set(normalized, code)
        self._code_to_url.set(code, normalized)
        return code

    def expand(self, code: str) -> str:
        return self._code_to_url.get(code)

    @property
    def table(self) -> HashTable[str]:
        return self._url_to_code

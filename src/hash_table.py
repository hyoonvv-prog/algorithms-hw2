"""A string-keyed hash table using separate chaining and Horner hashing."""

from dataclasses import dataclass
from typing import Generic, Iterator, TypeVar


Value = TypeVar("Value")


@dataclass
class _Node(Generic[Value]):
    key: str
    value: Value
    next: "_Node[Value] | None" = None


class HashTable(Generic[Value]):
    def __init__(self, capacity: int = 101) -> None:
        if type(capacity) is not int:
            raise TypeError("capacity must be an integer")
        if capacity <= 0:
            raise ValueError("capacity must be positive")
        self.capacity = capacity
        self._buckets: list[_Node[Value] | None] = [None] * capacity
        self._size = 0

    @staticmethod
    def _validate_key(key: str) -> None:
        if not isinstance(key, str):
            raise TypeError("key must be a string")

    def hash_steps(self, key: str) -> list[tuple[str, int, int, int]]:
        self._validate_key(key)
        steps = []
        current = 0
        for character in key:
            codepoint = ord(character)
            updated = (31 * current + codepoint) % self.capacity
            steps.append((character, current, codepoint, updated))
            current = updated
        return steps

    def _index(self, key: str) -> int:
        steps = self.hash_steps(key)
        return steps[-1][3] if steps else 0

    def _find_node(self, key: str) -> tuple[_Node[Value] | None, int]:
        self._validate_key(key)
        node = self._buckets[self._index(key)]
        comparisons = 0
        while node is not None:
            comparisons += 1
            if node.key == key:
                return node, comparisons
            node = node.next
        return None, comparisons

    def find(self, key: str) -> tuple[bool, Value | None, int]:
        node, comparisons = self._find_node(key)
        if node is None:
            return False, None, comparisons
        return True, node.value, comparisons

    def set(self, key: str, value: Value) -> None:
        self._validate_key(key)
        index = self._index(key)
        node = self._buckets[index]
        if node is None:
            self._buckets[index] = _Node(key, value)
            self._size += 1
            return

        while True:
            if node.key == key:
                node.value = value
                return
            if node.next is None:
                node.next = _Node(key, value)
                self._size += 1
                return
            node = node.next

    def get(self, key: str) -> Value:
        node, _ = self._find_node(key)
        if node is None:
            raise KeyError(key)
        return node.value

    def delete(self, key: str) -> None:
        self._validate_key(key)
        index = self._index(key)
        previous = None
        node = self._buckets[index]
        while node is not None:
            if node.key == key:
                if previous is None:
                    self._buckets[index] = node.next
                else:
                    previous.next = node.next
                self._size -= 1
                return
            previous = node
            node = node.next
        raise KeyError(key)

    def bucket_contents(self) -> list[list[str]]:
        contents = []
        for head in self._buckets:
            keys = []
            node = head
            while node is not None:
                keys.append(node.key)
                node = node.next
            contents.append(keys)
        return contents

    def items(self) -> Iterator[tuple[str, Value]]:
        for head in self._buckets:
            node = head
            while node is not None:
                yield node.key, node.value
                node = node.next

    def __len__(self) -> int:
        return self._size

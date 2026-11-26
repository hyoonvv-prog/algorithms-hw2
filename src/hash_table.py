"""A string-keyed hash table using separate chaining and Horner hashing."""

from dataclasses import dataclass
from typing import Generic, Iterator, TypeVar


Value = TypeVar("Value")


def _horner_hash_steps(key: str, capacity: int) -> list[tuple[str, int, int, int]]:
    steps = []
    current = 0
    for character in key:
        codepoint = ord(character)
        updated = (31 * current + codepoint) % capacity
        steps.append((character, current, codepoint, updated))
        current = updated
    return steps


@dataclass
class _Node(Generic[Value]):
    key: str
    value: Value
    next: "_Node[Value] | None" = None


class HashTable(Generic[Value]):
    def __init__(self, capacity: int = 101, max_load: float | None = 1.0) -> None:
        if type(capacity) is not int:
            raise TypeError("capacity must be an integer")
        if capacity <= 0:
            raise ValueError("capacity must be positive")
        self.capacity = capacity
        self.max_load = max_load
        self._buckets: list[_Node[Value] | None] = [None] * capacity
        self._size = 0

    @staticmethod
    def _validate_key(key: str) -> None:
        if not isinstance(key, str):
            raise TypeError("key must be a string")

    def hash_steps(self, key: str) -> list[tuple[str, int, int, int]]:
        self._validate_key(key)
        return _horner_hash_steps(key, self.capacity)

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
        previous = None
        while node is not None:
            if node.key == key:
                node.value = value
                return
            previous = node
            node = node.next

        if (
            self.max_load is not None
            and (self._size + 1) / self.capacity > self.max_load
        ):
            raise OverflowError("hash table max_load exceeded")

        new_node = _Node(key, value)
        if previous is None:
            self._buckets[index] = new_node
        else:
            previous.next = new_node
        self._size += 1

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

    def lookup_steps(self, key: str) -> list[tuple[int, str]]:
        self._validate_key(key)
        index = self._index(key)
        steps = []
        node = self._buckets[index]
        if node is None:
            return [(index, "empty")]
        while node is not None:
            steps.append((index, node.key))
            if node.key == key:
                break
            node = node.next
        return steps

    def items(self) -> Iterator[tuple[str, Value]]:
        for head in self._buckets:
            node = head
            while node is not None:
                yield node.key, node.value
                node = node.next

    def __len__(self) -> int:
        return self._size


@dataclass
class _Entry(Generic[Value]):
    key: str
    value: Value


_DELETED = object()


class LinearProbingHashTable(Generic[Value]):
    """A fixed-capacity hash table that resolves collisions by linear probing."""

    def __init__(self, capacity: int = 101) -> None:
        if type(capacity) is not int:
            raise TypeError("capacity must be an integer")
        if capacity <= 0:
            raise ValueError("capacity must be positive")
        self.capacity = capacity
        self._slots: list[_Entry[Value] | object | None] = [None] * capacity
        self._size = 0

    @staticmethod
    def _validate_key(key: str) -> None:
        if not isinstance(key, str):
            raise TypeError("key must be a string")

    def hash_steps(self, key: str) -> list[tuple[str, int, int, int]]:
        self._validate_key(key)
        return _horner_hash_steps(key, self.capacity)

    def _index(self, key: str) -> int:
        steps = self.hash_steps(key)
        return steps[-1][3] if steps else 0

    def _search(
        self, key: str
    ) -> tuple[_Entry[Value] | None, list[tuple[int, str]]]:
        self._validate_key(key)
        steps = []
        start = self._index(key)
        for offset in range(self.capacity):
            index = (start + offset) % self.capacity
            slot = self._slots[index]
            if slot is None:
                steps.append((index, "empty"))
                return None, steps
            if slot is _DELETED:
                steps.append((index, "deleted"))
                continue
            if not isinstance(slot, _Entry):
                raise RuntimeError("invalid slot state")
            steps.append((index, slot.key))
            if slot.key == key:
                return slot, steps
        return None, steps

    def find(self, key: str) -> tuple[bool, Value | None, int]:
        entry, steps = self._search(key)
        if entry is None:
            return False, None, len(steps)
        return True, entry.value, len(steps)

    def lookup_steps(self, key: str) -> list[tuple[int, str]]:
        _, steps = self._search(key)
        return steps

    def set(self, key: str, value: Value) -> None:
        self._validate_key(key)
        start = self._index(key)
        first_deleted = None
        for offset in range(self.capacity):
            index = (start + offset) % self.capacity
            slot = self._slots[index]
            if slot is None:
                target = first_deleted if first_deleted is not None else index
                self._slots[target] = _Entry(key, value)
                self._size += 1
                return
            if slot is _DELETED:
                if first_deleted is None:
                    first_deleted = index
                continue
            if not isinstance(slot, _Entry):
                raise RuntimeError("invalid slot state")
            if slot.key == key:
                slot.value = value
                return
        if first_deleted is not None:
            self._slots[first_deleted] = _Entry(key, value)
            self._size += 1
            return
        raise OverflowError("hash table is full")

    def get(self, key: str) -> Value:
        entry, _ = self._search(key)
        if entry is None:
            raise KeyError(key)
        return entry.value

    def delete(self, key: str) -> None:
        entry, steps = self._search(key)
        if entry is None:
            raise KeyError(key)
        index = steps[-1][0]
        self._slots[index] = _DELETED
        self._size -= 1

    def bucket_contents(self) -> list[list[str]]:
        contents = []
        for slot in self._slots:
            if isinstance(slot, _Entry):
                contents.append([slot.key])
            else:
                contents.append([])
        return contents

    def slot_contents(self) -> list[tuple[str, str | None]]:
        contents = []
        for slot in self._slots:
            if slot is None:
                contents.append(("empty", None))
            elif slot is _DELETED:
                contents.append(("deleted", None))
            elif isinstance(slot, _Entry):
                contents.append(("occupied", slot.key))
            else:
                raise RuntimeError("invalid slot state")
        return contents

    def items(self) -> Iterator[tuple[str, Value]]:
        for slot in self._slots:
            if isinstance(slot, _Entry):
                yield slot.key, slot.value

    def __len__(self) -> int:
        return self._size

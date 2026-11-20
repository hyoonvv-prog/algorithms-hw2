import unittest

from src.hash_table import HashTable


class HashTableTests(unittest.TestCase):
    def test_empty_key_and_empty_table(self):
        table = HashTable(capacity=5)
        self.assertEqual(len(table), 0)
        table.set("", "empty")
        self.assertEqual(table.get(""), "empty")
        self.assertEqual(len(table), 1)

    def test_collisions_are_searched_and_values_can_be_updated(self):
        table = HashTable(capacity=2)
        table.set("a", 1)
        table.set("c", 2)
        table.set("a", 3)
        self.assertEqual(table.get("a"), 3)
        self.assertEqual(table.get("c"), 2)
        self.assertEqual(len(table), 2)

    def test_delete_handles_head_middle_and_tail(self):
        table = HashTable(capacity=1)
        for key in ("first", "middle", "last"):
            table.set(key, key)
        for key in ("middle", "first", "last"):
            table.delete(key)
            with self.subTest(key=key), self.assertRaises(KeyError):
                table.get(key)
        self.assertEqual(len(table), 0)

    def test_missing_keys_raise_key_error(self):
        table = HashTable(capacity=3)
        with self.assertRaises(KeyError):
            table.get("missing")
        with self.assertRaises(KeyError):
            table.delete("missing")

    def test_hash_trace_exposes_horner_calculation(self):
        table = HashTable(capacity=7)
        self.assertEqual(table.hash_steps("ab"), [
            ("a", 0, ord("a"), (31 * 0 + ord("a")) % 7),
            ("b", (31 * 0 + ord("a")) % 7, ord("b"),
             (31 * ((31 * 0 + ord("a")) % 7) + ord("b")) % 7),
        ])

    def test_invalid_key_and_capacity_are_rejected(self):
        for capacity in (0, -1):
            with self.subTest(capacity=capacity), self.assertRaises(ValueError):
                HashTable(capacity=capacity)
        table = HashTable(capacity=3)
        with self.assertRaises(TypeError):
            table.set(1, "value")
        with self.assertRaises(TypeError):
            table.get(1)


if __name__ == "__main__":
    unittest.main()

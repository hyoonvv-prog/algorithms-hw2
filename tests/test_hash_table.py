import unittest

from src.hash_table import HashTable, LinearProbingHashTable


TABLE_TYPES = (HashTable, LinearProbingHashTable)


class HashTableTests(unittest.TestCase):
    def test_empty_key_and_empty_table(self):
        for table_type in TABLE_TYPES:
            with self.subTest(table_type=table_type.__name__):
                table = table_type(capacity=5)
                self.assertEqual(len(table), 0)
                table.set("", "empty")
                self.assertEqual(table.get(""), "empty")
                self.assertEqual(len(table), 1)

    def test_collisions_are_searched_and_values_can_be_updated(self):
        for table_type in TABLE_TYPES:
            with self.subTest(table_type=table_type.__name__):
                table = table_type(capacity=5)
                table.set("c", 1)
                table.set("h", 2)
                table.set("c", 3)
                self.assertEqual(table.get("c"), 3)
                self.assertEqual(table.get("h"), 2)
                self.assertEqual(len(table), 2)

    def test_delete_handles_head_middle_and_tail(self):
        for table_type in TABLE_TYPES:
            with self.subTest(table_type=table_type.__name__):
                table = table_type(capacity=5)
                for key in ("c", "h", "m"):
                    table.set(key, key)
                for key in ("h", "c", "m"):
                    table.delete(key)
                    with self.subTest(key=key), self.assertRaises(KeyError):
                        table.get(key)
                self.assertEqual(len(table), 0)

    def test_missing_keys_raise_key_error(self):
        for table_type in TABLE_TYPES:
            with self.subTest(table_type=table_type.__name__):
                table = table_type(capacity=3)
                with self.assertRaises(KeyError):
                    table.get("missing")
                with self.assertRaises(KeyError):
                    table.delete("missing")

    def test_hash_trace_exposes_horner_calculation(self):
        for table_type in TABLE_TYPES:
            with self.subTest(table_type=table_type.__name__):
                table = table_type(capacity=7)
                self.assertEqual(table.hash_steps("ab"), [
                    ("a", 0, ord("a"), (31 * 0 + ord("a")) % 7),
                    ("b", (31 * 0 + ord("a")) % 7, ord("b"),
                     (31 * ((31 * 0 + ord("a")) % 7) + ord("b")) % 7),
                ])

    def test_invalid_key_and_capacity_are_rejected(self):
        for table_type in TABLE_TYPES:
            for capacity in (0, -1):
                with self.subTest(table_type=table_type.__name__, capacity=capacity):
                    with self.assertRaises(ValueError):
                        table_type(capacity=capacity)
            table = table_type(capacity=3)
            with self.subTest(table_type=table_type.__name__):
                with self.assertRaises(TypeError):
                    table.set(1, "value")
                with self.assertRaises(TypeError):
                    table.get(1)

    def test_default_max_load_allows_load_one_but_rejects_overflow(self):
        for table_type in TABLE_TYPES:
            with self.subTest(table_type=table_type.__name__):
                table = table_type(capacity=2)
                table.set("first", 1)
                table.set("second", 2)

                with self.assertRaises(OverflowError):
                    table.set("third", 3)

                self.assertEqual(len(table), 2)

    def test_max_load_boundary_and_existing_key_update(self):
        for table_type in TABLE_TYPES:
            with self.subTest(table_type=table_type.__name__):
                table = table_type(capacity=4, max_load=0.5)
                table.set("first", 1)
                table.set("second", 2)
                table.set("first", 10)

                self.assertEqual(table.get("first"), 10)
                self.assertEqual(len(table), 2)
                with self.assertRaises(OverflowError):
                    table.set("third", 3)

    def test_none_max_load_has_no_limit(self):
        with self.subTest(table_type=HashTable.__name__):
            table = HashTable(capacity=1, max_load=None)
            for key in ("first", "second", "third"):
                table.set(key, key)

            self.assertEqual(len(table), 3)
            self.assertEqual(table.get("third"), "third")

        with self.subTest(table_type=LinearProbingHashTable.__name__):
            table = LinearProbingHashTable(capacity=3)
            for key in ("first", "second", "third"):
                table.set(key, key)

            self.assertEqual(len(table), 3)
            self.assertEqual(table.get("third"), "third")
            with self.assertRaises(OverflowError):
                table.set("fourth", "fourth")


if __name__ == "__main__":
    unittest.main()

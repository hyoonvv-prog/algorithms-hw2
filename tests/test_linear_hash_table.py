import unittest

from src.hash_table import LinearProbingHashTable


class LinearProbingHashTableTests(unittest.TestCase):
    def test_collisions_wrap_from_last_slot_to_first(self):
        table = LinearProbingHashTable(capacity=5)
        table.set("c", "last")
        table.set("h", "wrapped")

        self.assertEqual(table.bucket_contents(), [["h"], [], [], [], ["c"]])
        self.assertEqual(table.get("c"), "last")
        self.assertEqual(table.get("h"), "wrapped")
        self.assertEqual(table.lookup_steps("h"), [(4, "c"), (0, "h")])

    def test_deletion_preserves_search_and_tombstone_can_be_reused(self):
        table = LinearProbingHashTable(capacity=5)
        table.set("c", "first")
        table.set("h", "second")
        table.delete("c")

        self.assertEqual(table.slot_contents()[4], ("deleted", None))
        self.assertEqual(table.get("h"), "second")
        self.assertEqual(table.lookup_steps("h"), [(4, "deleted"), (0, "h")])
        table.set("m", "replacement")
        self.assertEqual(table.get("m"), "replacement")
        self.assertEqual(table.bucket_contents(), [["h"], [], [], [], ["m"]])
        self.assertEqual(table.slot_contents()[4], ("occupied", "m"))
        self.assertEqual(len(table), 2)

    def test_full_table_terminates_missing_search_and_rejects_new_key(self):
        table = LinearProbingHashTable(capacity=2)
        table.set("a", 1)
        table.set("b", 2)

        self.assertEqual(table.find("x"), (False, None, 2))
        with self.assertRaises(OverflowError):
            table.set("c", 3)
        table.set("a", 4)
        self.assertEqual(table.get("a"), 4)

    def test_empty_key_and_missing_keys(self):
        table = LinearProbingHashTable(capacity=1)
        table.set("", "empty")
        self.assertEqual(table.get(""), "empty")
        with self.assertRaises(KeyError):
            table.get("missing")
        with self.assertRaises(KeyError):
            table.delete("missing")

    def test_invalid_key_and_capacity_are_rejected(self):
        for capacity in (0, -1):
            with self.subTest(capacity=capacity), self.assertRaises(ValueError):
                LinearProbingHashTable(capacity=capacity)
        table = LinearProbingHashTable(capacity=3)
        with self.assertRaises(TypeError):
            table.set(1, "value")
        with self.assertRaises(TypeError):
            table.get(1)


if __name__ == "__main__":
    unittest.main()

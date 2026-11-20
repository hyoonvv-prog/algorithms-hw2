import unittest

from src.base62 import decode, encode


class Base62Tests(unittest.TestCase):
    def test_encode_zero(self):
        self.assertEqual(encode(0), "0")

    def test_encode_known_values(self):
        self.assertEqual(encode(61), "Z")
        self.assertEqual(encode(62), "10")
        self.assertEqual(encode(3843), "ZZ")

    def test_round_trip(self):
        for value in (0, 1, 61, 62, 3843, 10**30):
            with self.subTest(value=value):
                self.assertEqual(decode(encode(value)), value)

    def test_decode_zero_with_leading_zeroes(self):
        self.assertEqual(decode("000"), 0)

    def test_encode_rejects_negative_and_non_integer_values(self):
        with self.assertRaises(ValueError):
            encode(-1)
        for value in (True, 1.5, "12"):
            with self.subTest(value=value), self.assertRaises(TypeError):
                encode(value)

    def test_decode_rejects_empty_and_invalid_input(self):
        for code in ("", "a-b", "é"):
            with self.subTest(code=code), self.assertRaises(ValueError):
                decode(code)
        with self.assertRaises(TypeError):
            decode(12)


if __name__ == "__main__":
    unittest.main()

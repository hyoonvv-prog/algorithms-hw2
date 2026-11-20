import unittest

from src.shortener import Shortener


class ShortenerTests(unittest.TestCase):
    def test_shorten_and_expand_and_reuse_duplicate_url(self):
        shortener = Shortener(capacity=5)
        code = shortener.shorten("https://example.com/path")
        self.assertEqual(code, "0")
        self.assertEqual(shortener.expand(code), "https://example.com/path")
        self.assertEqual(shortener.shorten("https://example.com/path"), code)
        self.assertEqual(shortener.shorten(" https://example.org "), "1")

    def test_url_is_trimmed_and_invalid_inputs_are_rejected(self):
        shortener = Shortener()
        self.assertEqual(shortener.shorten("  http://example.com/a  "), "0")
        for url in ("", "example.com", "ftp://example.com", "https://", "https://bad host"):
            with self.subTest(url=url), self.assertRaises(ValueError):
                shortener.shorten(url)

    def test_unknown_code_raises_key_error(self):
        with self.assertRaises(KeyError):
            Shortener().expand("not-found")

    def test_invalid_table_type_is_rejected(self):
        with self.assertRaises(ValueError):
            Shortener(table_type="unknown")

    def test_linear_table_shortens_expands_and_reuses_duplicate_url(self):
        shortener = Shortener(table_type="linear", capacity=5)

        code = shortener.shorten("https://example.com")

        self.assertEqual(code, "0")
        self.assertEqual(shortener.expand(code), "https://example.com")
        self.assertEqual(shortener.shorten("https://example.com"), code)

    def test_both_table_types_reject_overflow(self):
        for table_type in ("chaining", "linear"):
            with self.subTest(table_type=table_type):
                shortener = Shortener(table_type=table_type, capacity=1)
                shortener.shorten("https://example.com")
                with self.assertRaises(OverflowError):
                    shortener.shorten("https://example.org")


if __name__ == "__main__":
    unittest.main()

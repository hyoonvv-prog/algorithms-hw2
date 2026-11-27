import unittest

from src.base62 import decode
from src.shortener import Shortener


TABLE_TYPES = ("chaining", "linear")


class ShortenerTests(unittest.TestCase):
    def test_shorten_and_expand_and_reuse_duplicate_url(self):
        for table_type in TABLE_TYPES:
            with self.subTest(table_type=table_type):
                shortener = Shortener(table_type=table_type, capacity=5)
                code = shortener.shorten("https://example.com/path")
                self.assertEqual(code, "0")
                self.assertEqual(shortener.expand(code), "https://example.com/path")
                self.assertEqual(shortener.shorten("https://example.com/path"), code)
                self.assertEqual(shortener.shorten(" https://example.org "), "1")

    def test_url_is_trimmed_and_invalid_inputs_are_rejected(self):
        for table_type in TABLE_TYPES:
            with self.subTest(table_type=table_type):
                shortener = Shortener(table_type=table_type)
                self.assertEqual(shortener.shorten("  http://example.com/a  "), "0")
                for url in ("", "example.com", "ftp://example.com", "https://", "https://bad host"):
                    with self.subTest(url=url), self.assertRaises(ValueError):
                        shortener.shorten(url)

    def test_scheme_and_host_case_variants_reuse_the_same_code(self):
        for table_type in TABLE_TYPES:
            with self.subTest(table_type=table_type):
                shortener = Shortener(table_type=table_type)
                code = shortener.shorten("HTTPS://Example.COM/Path")

                self.assertEqual(shortener.shorten("https://example.com/Path"), code)

    def test_reserved_table_path_is_skipped_when_issuing_codes(self):
        for table_type in TABLE_TYPES:
            with self.subTest(table_type=table_type):
                shortener = Shortener(table_type=table_type)
                shortener._next_id = decode("table")

                code = shortener.shorten("https://example.com")

                self.assertNotEqual(code, "table")
                self.assertEqual(shortener.expand(code), "https://example.com")

    def test_path_case_variants_receive_different_codes(self):
        for table_type in TABLE_TYPES:
            with self.subTest(table_type=table_type):
                shortener = Shortener(table_type=table_type)

                upper_path_code = shortener.shorten("https://example.com/Path")
                lower_path_code = shortener.shorten("https://example.com/path")

                self.assertNotEqual(upper_path_code, lower_path_code)

    def test_unknown_code_raises_key_error(self):
        for table_type in TABLE_TYPES:
            with self.subTest(table_type=table_type):
                with self.assertRaises(KeyError):
                    Shortener(table_type=table_type).expand("not-found")

    def test_invalid_table_type_is_rejected(self):
        with self.assertRaises(ValueError):
            Shortener(table_type="unknown")

    def test_both_table_types_shorten_expand_and_reuse_duplicate_url(self):
        for table_type in TABLE_TYPES:
            with self.subTest(table_type=table_type):
                shortener = Shortener(table_type=table_type, capacity=5)

                code = shortener.shorten("https://example.com")

                self.assertEqual(code, "0")
                self.assertEqual(shortener.expand(code), "https://example.com")
                self.assertEqual(shortener.shorten("https://example.com"), code)

    def test_both_table_types_reject_overflow(self):
        for table_type in TABLE_TYPES:
            with self.subTest(table_type=table_type):
                shortener = Shortener(table_type=table_type, capacity=1)
                shortener.shorten("https://example.com")
                with self.assertRaises(OverflowError):
                    shortener.shorten("https://example.org")


if __name__ == "__main__":
    unittest.main()

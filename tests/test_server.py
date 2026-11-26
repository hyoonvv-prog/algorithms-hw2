import http.client
import threading
import unittest

from src.server import create_server
from src.shortener import Shortener


class ServerTests(unittest.TestCase):
    def setUp(self):
        self.server = create_server("127.0.0.1", 0)
        self.thread = threading.Thread(target=self.server.serve_forever)
        self.thread.start()
        self.connection = http.client.HTTPConnection(
            "127.0.0.1", self.server.server_port
        )

    def tearDown(self):
        self.connection.close()
        self.server.shutdown()
        self.thread.join()
        self.server.server_close()

    def request(self, method, path, body=None, headers=None):
        self.connection.request(method, path, body=body, headers=headers or {})
        response = self.connection.getresponse()
        return response.status, dict(response.getheaders()), response.read().decode()

    def test_home_page_has_url_form(self):
        status, _, body = self.request("GET", "/")

        self.assertEqual(status, 200)
        self.assertIn('<form method="post" action="/">', body)
        self.assertIn('name="url"', body)

    def test_post_creates_result_and_redirect_resolves_code(self):
        body = "url=https%3A%2F%2Fexample.com%2Fpage"
        status, _, result = self.request(
            "POST",
            "/",
            body,
            {"Content-Type": "application/x-www-form-urlencoded"},
        )
        self.assertEqual(status, 200)
        self.assertIn("https://example.com/page", result)

        status, headers, _ = self.request("GET", "/0")
        self.assertEqual(status, 302)
        self.assertEqual(headers["Location"], "https://example.com/page")

    def test_result_link_uses_host_header_when_forwarded_host_is_absent(self):
        status, _, result = self.request(
            "POST",
            "/",
            "url=https%3A%2F%2Fexample.com",
            {
                "Content-Type": "application/x-www-form-urlencoded",
                "Host": "short.example:8000",
            },
        )

        self.assertEqual(status, 200)
        self.assertIn('href="//short.example:8000/0"', result)

    def test_result_link_prefers_forwarded_host(self):
        status, _, result = self.request(
            "POST",
            "/",
            "url=https%3A%2F%2Fexample.com",
            {
                "Content-Type": "application/x-www-form-urlencoded",
                "Host": "internal.example:8000",
                "X-Forwarded-Host": "public.example",
            },
        )

        self.assertEqual(status, 200)
        self.assertIn('href="//public.example/0"', result)
        self.assertNotIn("//internal.example:8000/0", result)

    def test_invalid_url_is_shown_as_client_error(self):
        status, _, body = self.request(
            "POST",
            "/",
            "url=not-a-url",
            {"Content-Type": "application/x-www-form-urlencoded"},
        )

        self.assertEqual(status, 400)
        self.assertIn("valid HTTP or HTTPS URL", body)

    def test_table_page_shows_bucket_and_hash_calculation(self):
        self.request(
            "POST",
            "/",
            "url=https%3A%2F%2Fexample.com",
            {"Content-Type": "application/x-www-form-urlencoded"},
        )

        status, _, body = self.request("GET", "/table")

        self.assertEqual(status, 200)
        self.assertIn("Bucket", body)
        self.assertIn("Horner", body)
        self.assertIn("https://example.com", body)

    def test_linear_table_page_shows_inspected_slots(self):
        server = create_server(
            "127.0.0.1", 0, Shortener(table_type="linear", capacity=7)
        )
        thread = threading.Thread(target=server.serve_forever)
        thread.start()
        connection = http.client.HTTPConnection("127.0.0.1", server.server_port)
        try:
            connection.request(
                "POST",
                "/",
                "url=https%3A%2F%2Fexample.com",
                {"Content-Type": "application/x-www-form-urlencoded"},
            )
            response = connection.getresponse()
            response.read()
            connection.request("GET", "/table")
            response = connection.getresponse()
            body = response.read().decode()

            self.assertEqual(response.status, 200)
            self.assertIn("Backend: linear", body)
            self.assertIn("Inspected positions:", body)
            self.assertIn("Horner", body)
        finally:
            connection.close()
            server.shutdown()
            thread.join()
            server.server_close()

    def test_unknown_code_returns_not_found(self):
        status, _, body = self.request("GET", "/missing")

        self.assertEqual(status, 404)
        self.assertIn("not found", body.lower())


if __name__ == "__main__":
    unittest.main()

"""HTTP interface for the in-memory URL shortener."""

import argparse
import html
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, unquote, urlsplit

from src.hash_table import HashTable, LinearProbingHashTable
from src.shortener import Shortener

Table = HashTable[str] | LinearProbingHashTable[str]


def _render_hash_steps(table: Table, key: str) -> str:
    steps = table.hash_steps(key)
    if not steps:
        return "empty key -> bucket 0"
    parts = ["h0 = 0"]
    for index, (character, previous, codepoint, result) in enumerate(steps, start=1):
        parts.append(
            f"h{index} = (31 * {previous} + {codepoint} "
            f"[{html.escape(character)}]) mod {table.capacity} = {result}"
        )
    return "; ".join(parts)


def _render_table(shortener: Shortener) -> str:
    rows = []
    slot_states = (
        shortener.table.slot_contents() if shortener.table_type == "linear" else None
    )
    for index, keys in enumerate(shortener.table.bucket_contents()):
        key_details = []
        for key in keys:
            escaped_key = html.escape(key)
            calculation = _render_hash_steps(shortener.table, key)
            lookup = " -> ".join(
                f"{position}: {html.escape(inspected)}"
                for position, inspected in shortener.table.lookup_steps(key)
            )
            key_details.append(
                f"<li><code>{escaped_key}</code><br>{calculation}"
                f"<br>Inspected positions: {lookup}</li>"
            )
        if key_details:
            contents = "<ul>" + "".join(key_details) + "</ul>"
        elif slot_states is not None:
            contents = slot_states[index][0]
        else:
            contents = "empty"
        rows.append(f"<tr><th>{index}</th><td>{contents}</td></tr>")
    position_label = "Slot" if shortener.table_type == "linear" else "Bucket"
    return (
        "<!doctype html><html lang=\"en\"><meta charset=\"utf-8\">"
        "<title>Hash table</title><h1>Hash table</h1>"
        f"<p>Backend: {html.escape(shortener.table_type)}; "
        f"capacity: {shortener.capacity}</p>"
        f"<table><thead><tr><th>{position_label}</th>"
        "<th>Keys, lookup path, and Horner calculation</th></tr></thead><tbody>"
        + "".join(rows)
        + "</tbody></table><p><a href=\"/\">Shorten another URL</a></p></html>"
    )


def create_server(
    host: str, port: int, shortener: Shortener | None = None
) -> HTTPServer:
    active_shortener = shortener or Shortener()

    class Handler(BaseHTTPRequestHandler):
        def _send_html(self, status: int, content: str) -> None:
            payload = content.encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def _error_page(self, status: int, message: str) -> None:
            self._send_html(
                status,
                "<!doctype html><html lang=\"en\"><meta charset=\"utf-8\">"
                f"<title>Error</title><h1>Error</h1><p>{html.escape(message)}</p>"
                "<p><a href=\"/\">Return to the form</a></p></html>",
            )

        def do_GET(self) -> None:
            path = urlsplit(self.path).path
            if path == "/":
                self._send_html(
                    200,
                    "<!doctype html><html lang=\"en\"><meta charset=\"utf-8\">"
                    "<title>URL shortener</title><h1>URL shortener</h1>"
                    "<form method=\"post\" action=\"/\">"
                    "<label>URL <input type=\"url\" name=\"url\" required></label>"
                    "<button type=\"submit\">Shorten</button></form>"
                    "<p><a href=\"/table\">Inspect hash table</a></p></html>",
                )
                return
            if path == "/table":
                self._send_html(200, _render_table(active_shortener))
                return
            code = unquote(path.lstrip("/"))
            if not code or "/" in code:
                self._error_page(404, "Short URL not found")
                return
            try:
                url = active_shortener.expand(code)
            except KeyError:
                self._error_page(404, "Short URL not found")
                return
            self.send_response(302)
            self.send_header("Location", url)
            self.send_header("Content-Length", "0")
            self.end_headers()

        def do_POST(self) -> None:
            if urlsplit(self.path).path != "/":
                self._error_page(404, "Page not found")
                return
            try:
                content_length = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                self._error_page(400, "Invalid form submission")
                return
            if content_length < 0 or content_length > 65536:
                self._error_page(400, "Invalid form submission")
                return
            try:
                form = self.rfile.read(content_length).decode("utf-8")
            except UnicodeDecodeError:
                self._error_page(400, "Form must be UTF-8 encoded")
                return
            url = parse_qs(form, keep_blank_values=True).get("url", [""])[0]
            try:
                code = active_shortener.shorten(url)
            except (TypeError, ValueError, OverflowError) as error:
                self._error_page(400, str(error))
                return
            escaped_url = html.escape(active_shortener.expand(code))
            escaped_code = html.escape(code)
            host = self.headers.get("X-Forwarded-Host") or self.headers.get("Host")
            short_link = (
                f"//{html.escape(host)}/{escaped_code}"
                if host
                else f"/{escaped_code}"
            )
            self._send_html(
                200,
                "<!doctype html><html lang=\"en\"><meta charset=\"utf-8\">"
                "<title>Short URL created</title><h1>Short URL created</h1>"
                f"<p>Original URL: <a href=\"{escaped_url}\">{escaped_url}</a></p>"
                f"<p>Short code: <code>{escaped_code}</code></p>"
                f"<p>Short link: <a href=\"{short_link}\">{short_link}</a></p>"
                "<p><a href=\"/\">Shorten another URL</a> | "
                "<a href=\"/table\">Inspect hash table</a></p></html>",
            )

    return HTTPServer((host, port), Handler)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the URL shortener web server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument(
        "--table-type", choices=("chaining", "linear"), default="chaining"
    )
    arguments = parser.parse_args()

    server = create_server(
        arguments.host,
        arguments.port,
        Shortener(table_type=arguments.table_type),
    )
    print(f"Serving on http://{arguments.host}:{server.server_port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()

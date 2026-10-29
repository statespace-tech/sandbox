"""A small shop for trying Statespace.

GET / shows the price, and the experiment and arm that served the request.
POST /buy buys one item and prints a JSON line on stdout.
"""

import json
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

# The change that the experiment "price" tests. A commit on a branch can
# lower the price.
PRICE = 12


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health":
            return self.reply(200, {"ok": True})
        if self.path != "/":
            return self.reply(404, {"error": "not found"})
        self.reply(
            200,
            {
                # The proxy sets these headers on requests of an arm.
                # Live gets none.
                "experiment": self.headers.get("x-statespace-experiment"),
                "arm": self.headers.get("x-statespace-arm"),
                "price": PRICE,
            },
        )

    def do_POST(self):
        if self.path != "/buy":
            return self.reply(404, {"error": "not found"})
        print(json.dumps({"event": "purchase", "amount": PRICE}), flush=True)
        self.reply(200, {"bought": 1, "price": PRICE})

    def reply(self, status, body):
        data = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, format, *args):
        print(f"{self.command} {self.path}", file=sys.stderr, flush=True)


def main():
    port = int(os.environ.get("PORT", "8000"))
    ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()


if __name__ == "__main__":
    main()

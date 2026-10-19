"""A small shop for trying Statespace. It says which arm served the request,
and prints a JSON line for each visit and purchase."""

import json
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

# The change an arm tests. An exp/ branch might lower the price.
PRICE = 14


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        subject = self.headers.get("x-statespace-subject")
        if self.path == "/health":
            return self.reply({"ok": True})
        if self.path.startswith("/buy") and subject:
            print(json.dumps({"event": "purchase", "subject": subject, "amount": PRICE}), flush=True)
        elif subject:
            print(json.dumps({"event": "visit", "subject": subject}), flush=True)
        self.reply(
            {
                "arm": self.headers.get("x-statespace-arm", "default"),
                "commit": os.environ.get("STATESPACE_COMMIT"),
                "price": PRICE,
            }
        )

    def reply(self, body):
        data = json.dumps(body).encode()
        self.send_response(200)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, format, *args):
        print(f"{self.command} {self.path}", file=sys.stderr, flush=True)


if __name__ == "__main__":
    ThreadingHTTPServer(("0.0.0.0", int(os.environ.get("PORT", "8000"))), Handler).serve_forever()

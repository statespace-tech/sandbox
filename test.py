"""Tests for the shop. Run them with `python3 test.py`."""

import json
import threading
import urllib.request
from http.server import ThreadingHTTPServer

import app

assert 0 < app.PRICE <= 100, f"the price must be between 1 and 100, not {app.PRICE}"

server = ThreadingHTTPServer(("127.0.0.1", 0), app.Handler)
threading.Thread(target=server.serve_forever, daemon=True).start()
base = f"http://127.0.0.1:{server.server_address[1]}"


def call(path, method="GET", headers=None):
    request = urllib.request.Request(base + path, method=method, headers=headers or {})
    with urllib.request.urlopen(request) as response:
        return json.load(response)


arm = {"x-statespace-experiment": "price", "x-statespace-arm": "a1b2c3d"}
page = call("/", headers=arm)
assert page == {"experiment": "price", "arm": "a1b2c3d", "price": app.PRICE}, page
page = call("/")
assert page == {"experiment": None, "arm": None, "price": app.PRICE}, page
assert call("/buy", method="POST") == {"bought": 1, "price": app.PRICE}
assert call("/health") == {"ok": True}

server.shutdown()
print("ok")

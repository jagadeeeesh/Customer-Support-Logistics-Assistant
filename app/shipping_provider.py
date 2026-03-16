from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread
from urllib.parse import urlparse


class ShippingRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802 (http method naming)
        parsed = urlparse(self.path)
        segments = parsed.path.strip("/").split("/")

        if len(segments) != 4 or segments[0] != "shipping":
            self.send_response(404)
            self.end_headers()
            return

        _, carrier, tracking_number, _ = segments[0], segments[1], segments[2], segments[3]
        now = datetime.now(timezone.utc)

        if tracking_number.endswith("84"):
            payload = {
                "tracking_number": tracking_number,
                "current_status": f"{carrier.upper()}:DELAYED",
                "latest_location": "Louisville, KY",
                "estimated_delivery_date": (now + timedelta(days=2)).isoformat(),
            }
        else:
            payload = {
                "tracking_number": tracking_number,
                "current_status": f"{carrier.upper()}:IN_TRANSIT",
                "latest_location": "Memphis, TN",
                "estimated_delivery_date": (now + timedelta(hours=8)).isoformat(),
            }

        body = json.dumps(payload).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt: str, *args) -> None:
        return


class ShippingProviderServer:
    def __init__(self, host: str = "127.0.0.1", port: int = 8100):
        self.server = HTTPServer((host, port), ShippingRequestHandler)
        self.thread = Thread(target=self.server.serve_forever, daemon=True)

    @property
    def base_url(self) -> str:
        host, port = self.server.server_address
        return f"http://{host}:{port}"

    def start(self) -> None:
        self.thread.start()

    def stop(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=1)

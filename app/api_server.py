from __future__ import annotations

import json
import re
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread
from typing import Any

from app.models import SupportRequest
from app.services import OrderNotFoundError, SupportAgentOrchestrator

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class SupportAPIHandler(BaseHTTPRequestHandler):
    orchestrator: SupportAgentOrchestrator

    def _send_json(self, status: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/health":
            self._send_json(HTTPStatus.OK, {"status": "ok"})
            return

        self._send_json(HTTPStatus.NOT_FOUND, {"error": "Not found"})

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/support/request":
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "Not found"})
            return

        content_length = int(self.headers.get("Content-Length", "0"))
        raw_body = self.rfile.read(content_length)

        try:
            payload = json.loads(raw_body.decode("utf-8"))
        except json.JSONDecodeError:
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": "Invalid JSON body"})
            return

        email = payload.get("email")
        if not isinstance(email, str) or not EMAIL_RE.match(email):
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": "email must be a valid address"})
            return

        customer_message = payload.get("customer_message", "Where is my order?")
        if not isinstance(customer_message, str):
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": "customer_message must be a string"})
            return

        try:
            response = self.orchestrator.handle_request(
                SupportRequest(email=email, customer_message=customer_message)
            )
        except OrderNotFoundError as exc:
            self._send_json(HTTPStatus.NOT_FOUND, {"error": str(exc)})
            return
        except RuntimeError as exc:
            self._send_json(HTTPStatus.BAD_GATEWAY, {"error": str(exc)})
            return

        self._send_json(HTTPStatus.OK, response.to_dict())

    def log_message(self, fmt: str, *args: Any) -> None:
        return


class SupportAPIServer:
    def __init__(self, orchestrator: SupportAgentOrchestrator, host: str = "127.0.0.1", port: int = 8000):
        handler_cls = type("ConfiguredSupportAPIHandler", (SupportAPIHandler,), {})
        handler_cls.orchestrator = orchestrator
        self.server = HTTPServer((host, port), handler_cls)
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

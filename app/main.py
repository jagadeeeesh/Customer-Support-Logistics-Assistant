from __future__ import annotations

import argparse
import json
import time

from app.api_server import SupportAPIServer
from app.database import DB_PATH, init_db, seed_data
from app.models import SupportRequest
from app.services import (
    BusinessRulesEngine,
    DiscountService,
    OrderRepository,
    ShippingAPIClient,
    SupportAgentOrchestrator,
)
from app.shipping_provider import ShippingProviderServer


def build_orchestrator(shipping_base_url: str) -> SupportAgentOrchestrator:
    return SupportAgentOrchestrator(
        repository=OrderRepository(DB_PATH),
        shipping_client=ShippingAPIClient(shipping_base_url),
        rules_engine=BusinessRulesEngine(),
        discount_service=DiscountService(),
    )


def run_demo(email: str) -> dict:
    init_db(DB_PATH)
    seed_data(DB_PATH)

    shipping_server = ShippingProviderServer()
    shipping_server.start()

    try:
        orchestrator = build_orchestrator(shipping_server.base_url)
        response = orchestrator.handle_request(SupportRequest(email=email))
        return response.__dict__
    finally:
        shipping_server.stop()


def run_http_server(host: str = "127.0.0.1", port: int = 8000) -> None:
    init_db(DB_PATH)
    seed_data(DB_PATH)

    shipping_server = ShippingProviderServer()
    shipping_server.start()

    orchestrator = build_orchestrator(shipping_server.base_url)
    api_server = SupportAPIServer(orchestrator, host=host, port=port)
    api_server.start()

    print(f"Support API running at {api_server.base_url}")
    print("POST /support/request with {'email':'alice@example.com'}")

    try:
        while True:
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass
    finally:
        api_server.stop()
        shipping_server.stop()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Customer Support & Logistics Assistant")
    parser.add_argument("--mode", choices=["demo", "serve"], default="demo")
    parser.add_argument("--email", default="alice@example.com")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    if args.mode == "serve":
        run_http_server(host=args.host, port=args.port)
    else:
        result = run_demo(args.email)
        print(json.dumps(result, indent=2, default=str))

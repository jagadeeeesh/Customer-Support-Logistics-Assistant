from __future__ import annotations

import json

from app.database import DB_PATH, init_db, seed_data
from app.models import SupportRequest
from app.services import (
    BusinessRulesEngine,
    DiscountService,
    OrderRepository,
    SupportAgentOrchestrator,
)
from app.shipping_provider import ShippingProviderServer
from app.services import ShippingAPIClient


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
        return {
            "customer_email": response.customer_email,
            "order_id": response.order_id,
            "tracking_number": response.tracking_number,
            "shipping_status": response.shipping_status,
            "latest_location": response.latest_location,
            "discount_code": response.discount_code,
            "message": response.message,
            "reasoning_steps": response.reasoning_steps,
        }
    finally:
        shipping_server.stop()


if __name__ == "__main__":
    result = run_demo("alice@example.com")
    print(json.dumps(result, indent=2, default=str))

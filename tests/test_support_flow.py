from pathlib import Path

from app.database import DB_PATH, init_db, seed_data
from app.models import SupportRequest
from app.services import (
    BusinessRulesEngine,
    DiscountService,
    OrderNotFoundError,
    OrderRepository,
    ShippingAPIClient,
    SupportAgentOrchestrator,
)
from app.shipping_provider import ShippingProviderServer

DB_FILE = Path(DB_PATH)


def build_orchestrator(base_url: str) -> SupportAgentOrchestrator:
    return SupportAgentOrchestrator(
        repository=OrderRepository(DB_PATH),
        shipping_client=ShippingAPIClient(base_url),
        rules_engine=BusinessRulesEngine(),
        discount_service=DiscountService(),
    )


def setup_function() -> None:
    if DB_FILE.exists():
        DB_FILE.unlink()
    init_db(DB_PATH)
    seed_data(DB_PATH)


def test_delayed_order_gets_discount_code() -> None:
    server = ShippingProviderServer(port=8101)
    server.start()
    try:
        orchestrator = build_orchestrator(server.base_url)
        response = orchestrator.handle_request(SupportRequest(email="alice@example.com"))
    finally:
        server.stop()

    assert response.order_id == "ORD-1001"
    assert response.discount_code is not None
    assert response.discount_code.startswith("SORRY10-")
    assert len(response.reasoning_steps) == 4


def test_on_time_order_has_no_discount() -> None:
    server = ShippingProviderServer(port=8102)
    server.start()
    try:
        orchestrator = build_orchestrator(server.base_url)
        response = orchestrator.handle_request(SupportRequest(email="bob@example.com"))
    finally:
        server.stop()

    assert response.order_id == "ORD-1002"
    assert response.discount_code is None


def test_unknown_customer_returns_not_found() -> None:
    server = ShippingProviderServer(port=8103)
    server.start()
    try:
        orchestrator = build_orchestrator(server.base_url)
        try:
            orchestrator.handle_request(SupportRequest(email="nobody@example.com"))
            raised = False
        except OrderNotFoundError:
            raised = True
    finally:
        server.stop()

    assert raised is True

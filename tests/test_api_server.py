import json
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from app.api_server import SupportAPIServer
from app.database import DB_PATH, init_db, seed_data
from app.services import (
    BusinessRulesEngine,
    DiscountService,
    OrderRepository,
    ShippingAPIClient,
    SupportAgentOrchestrator,
    LLMResponseComposer,
)
from app.shipping_provider import ShippingProviderServer

DB_FILE = Path(DB_PATH)


def setup_function() -> None:
    if DB_FILE.exists():
        DB_FILE.unlink()
    init_db(DB_PATH)
    seed_data(DB_PATH)


def build_orchestrator(shipping_base_url: str) -> SupportAgentOrchestrator:
    return SupportAgentOrchestrator(
        repository=OrderRepository(DB_PATH),
        shipping_client=ShippingAPIClient(shipping_base_url),
        rules_engine=BusinessRulesEngine(),
        discount_service=DiscountService(),
        llm_composer=LLMResponseComposer(api_key=None),
    )


def post_json(url: str, payload: dict) -> tuple[int, dict]:
    data = json.dumps(payload).encode("utf-8")
    req = Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urlopen(req, timeout=5) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except HTTPError as exc:
        return exc.code, json.loads(exc.read().decode("utf-8"))


def test_support_endpoint_delayed_order_with_discount_request() -> None:
    shipping = ShippingProviderServer(port=8111)
    shipping.start()
    orchestrator = build_orchestrator(shipping.base_url)
    api = SupportAPIServer(orchestrator, port=8211)
    api.start()

    try:
        status, body = post_json(
            f"{api.base_url}/support/request",
            {
                "email": "alice@example.com",
                "customer_message": "Where is my order and can I get a 10% discount code?",
            },
        )
    finally:
        api.stop()
        shipping.stop()

    assert status == 200
    assert body["order_id"] == "ORD-1001"
    assert body["discount_code"].startswith("SORRY10-")
    assert body["is_delayed"] is True


def test_support_endpoint_delayed_order_no_discount_without_request() -> None:
    shipping = ShippingProviderServer(port=8112)
    shipping.start()
    orchestrator = build_orchestrator(shipping.base_url)
    api = SupportAPIServer(orchestrator, port=8212)
    api.start()

    try:
        status, body = post_json(
            f"{api.base_url}/support/request",
            {"email": "alice@example.com", "customer_message": "Where is my order?"},
        )
    finally:
        api.stop()
        shipping.stop()

    assert status == 200
    assert body["discount_code"] is None


def test_support_endpoint_invalid_email() -> None:
    shipping = ShippingProviderServer(port=8113)
    shipping.start()
    orchestrator = build_orchestrator(shipping.base_url)
    api = SupportAPIServer(orchestrator, port=8213)
    api.start()

    try:
        status, body = post_json(f"{api.base_url}/support/request", {"email": "not-an-email"})
    finally:
        api.stop()
        shipping.stop()

    assert status == 400
    assert "valid address" in body["error"]

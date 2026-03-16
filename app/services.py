from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from urllib.error import HTTPError
from urllib.request import urlopen

from app.database import get_connection
from app.models import OrderRecord, ShippingDetails, SupportRequest, SupportResponse


class OrderNotFoundError(ValueError):
    pass


class OrderRepository:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def find_latest_order_by_email(self, email: str) -> OrderRecord:
        with get_connection(self.db_path) as conn:
            row = conn.execute(
                """
                SELECT *
                FROM orders
                WHERE customer_email = ?
                ORDER BY guaranteed_delivery_date DESC
                LIMIT 1
                """,
                (email,),
            ).fetchone()

        if row is None:
            raise OrderNotFoundError(f"No order found for {email}")

        return OrderRecord(
            order_id=row["order_id"],
            customer_email=row["customer_email"],
            carrier=row["carrier"],
            tracking_number=row["tracking_number"],
            guaranteed_delivery_date=datetime.fromisoformat(row["guaranteed_delivery_date"]),
            order_status=row["order_status"],
        )


class ShippingAPIClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")

    def fetch_realtime_status(self, carrier: str, tracking_number: str) -> ShippingDetails:
        url = f"{self.base_url}/shipping/{carrier}/{tracking_number}/status"
        try:
            with urlopen(url, timeout=5) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            raise RuntimeError(f"Shipping API request failed: {exc.code}") from exc

        return ShippingDetails(
            tracking_number=payload["tracking_number"],
            current_status=payload["current_status"],
            latest_location=payload["latest_location"],
            estimated_delivery_date=datetime.fromisoformat(payload["estimated_delivery_date"]),
        )


class BusinessRulesEngine:
    @staticmethod
    def is_delivery_delayed(
        guaranteed_delivery_date: datetime, estimated_delivery_date: datetime
    ) -> bool:
        return estimated_delivery_date > guaranteed_delivery_date


class DiscountService:
    @staticmethod
    def generate_discount_code(email: str, order_id: str, percent: int = 10) -> str:
        token_input = f"{email}:{order_id}:{percent}:{datetime.now(timezone.utc).isoformat()}"
        digest = hashlib.sha256(token_input.encode("utf-8")).hexdigest()[:8].upper()
        return f"SORRY{percent}-{digest}"


class SupportAgentOrchestrator:
    def __init__(
        self,
        repository: OrderRepository,
        shipping_client: ShippingAPIClient,
        rules_engine: BusinessRulesEngine,
        discount_service: DiscountService,
    ):
        self.repository = repository
        self.shipping_client = shipping_client
        self.rules_engine = rules_engine
        self.discount_service = discount_service

    def handle_request(self, request: SupportRequest) -> SupportResponse:
        reasoning_steps: list[str] = []

        reasoning_steps.append("Action 1: Query SQL database for customer order details.")
        order = self.repository.find_latest_order_by_email(request.email)

        reasoning_steps.append("Action 2: Call external shipping API for real-time status.")
        shipping = self.shipping_client.fetch_realtime_status(order.carrier, order.tracking_number)

        reasoning_steps.append("Action 3: Evaluate delay policy and generate discount if needed.")
        discount_code = None
        if self.rules_engine.is_delivery_delayed(
            order.guaranteed_delivery_date, shipping.estimated_delivery_date
        ):
            discount_code = self.discount_service.generate_discount_code(
                request.email, order.order_id, 10
            )

        reasoning_steps.append("Action 4: Compose final response to customer.")

        if discount_code:
            message = (
                f"Your order {order.order_id} is currently {shipping.current_status} near "
                f"{shipping.latest_location}. We are sorry for the delay. "
                f"Use discount code {discount_code} for 10% off your next order."
            )
        else:
            message = (
                f"Your order {order.order_id} is currently {shipping.current_status} near "
                f"{shipping.latest_location}. It's still within the guaranteed window."
            )

        return SupportResponse(
            customer_email=order.customer_email,
            order_id=order.order_id,
            tracking_number=order.tracking_number,
            carrier=order.carrier,
            order_status=order.order_status,
            shipping_status=shipping.current_status,
            latest_location=shipping.latest_location,
            estimated_delivery_date=shipping.estimated_delivery_date,
            discount_code=discount_code,
            message=message,
            reasoning_steps=reasoning_steps,
        )

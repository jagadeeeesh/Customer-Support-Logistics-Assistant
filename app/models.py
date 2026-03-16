from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime


@dataclass
class SupportRequest:
    email: str
    customer_message: str = "Where is my order?"


@dataclass
class OrderRecord:
    order_id: str
    customer_email: str
    carrier: str
    tracking_number: str
    guaranteed_delivery_date: datetime
    order_status: str


@dataclass
class ShippingDetails:
    tracking_number: str
    current_status: str
    latest_location: str
    estimated_delivery_date: datetime


@dataclass
class SupportResponse:
    customer_email: str
    order_id: str
    tracking_number: str
    carrier: str
    order_status: str
    shipping_status: str
    latest_location: str
    estimated_delivery_date: datetime
    guaranteed_delivery_date: datetime
    is_delayed: bool
    discount_code: str | None
    message: str
    reasoning_steps: list[str]

    def to_dict(self) -> dict:
        return asdict(self)

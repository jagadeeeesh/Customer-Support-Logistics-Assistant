from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone

DB_PATH = "support_assistant.db"


@contextmanager
def get_connection(db_path: str = DB_PATH):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def init_db(db_path: str = DB_PATH) -> None:
    with get_connection(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS orders (
                order_id TEXT PRIMARY KEY,
                customer_email TEXT NOT NULL,
                carrier TEXT NOT NULL,
                tracking_number TEXT NOT NULL,
                guaranteed_delivery_date TEXT NOT NULL,
                order_status TEXT NOT NULL
            )
            """
        )
        conn.commit()


def seed_data(db_path: str = DB_PATH) -> None:
    now = datetime.now(timezone.utc)
    sample_orders = [
        (
            "ORD-1001",
            "alice@example.com",
            "UPS",
            "1Z999AA10123456784",
            (now - timedelta(days=1)).isoformat(),
            "IN_TRANSIT",
        ),
        (
            "ORD-1002",
            "bob@example.com",
            "FedEx",
            "449044304137821",
            (now + timedelta(days=2)).isoformat(),
            "OUT_FOR_DELIVERY",
        ),
    ]

    with get_connection(db_path) as conn:
        for row in sample_orders:
            conn.execute(
                """
                INSERT OR IGNORE INTO orders (
                    order_id,
                    customer_email,
                    carrier,
                    tracking_number,
                    guaranteed_delivery_date,
                    order_status
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                row,
            )
        conn.commit()

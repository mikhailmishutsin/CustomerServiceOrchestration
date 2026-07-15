import json
from pathlib import Path
from typing import Any

from cs_orchestration.integrations.oms.base import FilterMode


class MockOmsClient:
    """Reads sanitized OMS examples instead of calling production OMS."""

    def __init__(self, fixture_path: Path) -> None:
        self.fixture_path = fixture_path
        self.last_request: dict[str, Any] | None = None
        self.last_request_debug: dict[str, Any] | None = None
        self.request_history: list[dict[str, Any]] = []

    def search_orders(
        self,
        *,
        customer_phone: str | None = None,
        customer_email: str | None = None,
        customer_full_name: str | None = None,
        order_number: str | None = None,
        filter_mode: FilterMode | None = None,
        order_status: str | None = None,
        order_status_fulfillment: str | None = None,
        marketplace: str | None = None,
        expand: bool = True,
        limit: int = 5,
    ) -> dict[str, Any]:
        self.last_request = {
            "customer_phone": customer_phone,
            "customer_email": customer_email,
            "customer_full_name": customer_full_name,
            "order_number": order_number,
            "filter_mode": filter_mode,
            "order_status": order_status,
            "order_status_fulfillment": order_status_fulfillment,
            "marketplace": marketplace,
            "expand": expand,
            "limit": limit,
        }
        self.request_history.append(self.last_request.copy())
        self.last_request_debug = {
            "service": "mock_order_business_api",
            "operation": "search",
            "method": "MOCK",
            "fixture_path": str(self.fixture_path),
            "query": self.last_request,
        }
        with self.fixture_path.open("r", encoding="utf-8") as fixture:
            payload = json.load(fixture)

        if limit >= 0:
            payload["orders"] = payload.get("orders", [])[:limit]
            payload["order_count"] = len(payload["orders"])
        return payload

    def get_order_details(
        self,
        *,
        order_number: str,
        expand: bool = True,
    ) -> dict[str, Any]:
        payload = self.search_orders(order_number=order_number, expand=expand, limit=1)
        return payload["orders"][0].get("details") or payload["orders"][0]

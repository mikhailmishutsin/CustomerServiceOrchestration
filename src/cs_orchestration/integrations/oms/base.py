from typing import Any, Literal, Protocol


FilterMode = Literal["all", "any"]


class OrderBusinessClient(Protocol):
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
        """Search orders in the Order Business API."""

    def get_order_details(
        self,
        *,
        order_number: str,
        expand: bool = True,
    ) -> dict[str, Any]:
        """Fetch one order's details from the Order Business API."""

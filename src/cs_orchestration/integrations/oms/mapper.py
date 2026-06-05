import re
from typing import Any

from cs_orchestration.domain.models import (
    Customer,
    DetailsRef,
    Order,
    OrderLine,
    PurchaseOrderLine,
    Shipment,
    ShippingAddress,
)


SECRET_KEY_PATTERN = re.compile(r"(secret_key=)[^&]+")


def normalize_search_orders_response(payload: dict[str, Any]) -> list[Order]:
    orders = [normalize_order(order) for order in payload.get("orders", [])]
    return sorted(orders, key=lambda order: order.order_date or "", reverse=True)


def normalize_order(raw_order: dict[str, Any]) -> Order:
    details = raw_order.get("details") or raw_order
    shipping_to = (details.get("shipping_information") or {}).get("to") or {}
    order_number = str(details.get("order_number") or raw_order.get("order_number"))

    lines = [normalize_order_line(line) for line in details.get("lines", [])]

    return Order(
        order_number=order_number,
        order_date=details.get("order_date") or raw_order.get("order_date"),
        marketplace=details.get("marketplace") or raw_order.get("marketplace"),
        order_status=details.get("order_status") or raw_order.get("order_status"),
        fulfillment_status=details.get("order_status_fulfillment")
        or raw_order.get("order_status_fulfillment"),
        customer=Customer(
            name=shipping_to.get("full_name"),
            email=shipping_to.get("email"),
            phone=shipping_to.get("phone"),
        ),
        shipping_address=ShippingAddress(
            line1=shipping_to.get("street1"),
            line2=shipping_to.get("street2"),
            city=shipping_to.get("city"),
            state=shipping_to.get("state"),
            postal_code=shipping_to.get("zip"),
            country=shipping_to.get("country") or "US",
        ),
        order_lines=lines,
        shipments=_extract_shipments(details),
        details_ref=DetailsRef(
            order_number=order_number,
            raw_details_url_redacted=redact_secret(raw_order.get("details_url")),
            safe_agent_url=None,
        ),
        totals={
            "currency": details.get("currency") or raw_order.get("currency"),
            "untaxed_total": _to_float(details.get("untaxed_total")),
            "tax_total": _to_float(details.get("tax_total")),
            "total_with_taxes": _to_float(details.get("total_with_taxes")),
        },
    )


def normalize_order_line(raw_line: dict[str, Any]) -> OrderLine:
    purchase_order_lines = [
        normalize_purchase_order_line(raw_pol)
        for raw_pol in raw_line.get("purchase_order_lines", [])
    ]
    fulfillment_status = next(
        (
            pol.fulfillment_status
            for pol in purchase_order_lines
            if pol.fulfillment_status is not None
        ),
        None,
    )

    return OrderLine(
        sku=raw_line.get("sku"),
        product_name=raw_line.get("description"),
        quantity=_to_int(raw_line.get("quantity")),
        price=_to_float(raw_line.get("price")),
        tax_amount=_to_float(raw_line.get("tax_amount")),
        tax_percent=_to_float(raw_line.get("tax_percent")),
        fulfillment_status=fulfillment_status,
        purchase_order_lines=purchase_order_lines,
    )


def normalize_purchase_order_line(raw_pol: dict[str, Any]) -> PurchaseOrderLine:
    shipping_information = raw_pol.get("shipping_information") or {}
    shipping_from = shipping_information.get("from") or {}
    tracking_information = shipping_information.get("tracking_information") or {}

    return PurchaseOrderLine(
        purchase_order_line_id=raw_pol.get("purchase_order_line_id"),
        purchase_order_number=raw_pol.get("purchase_order_number"),
        quantity=_to_int(raw_pol.get("quantity")),
        fulfillment_status=raw_pol.get("fulfillment_status"),
        supplier_name=shipping_from.get("supplier_name"),
        supplier_warehouse=shipping_from.get("supplier_warehouse"),
        supplier_price=_to_float(raw_pol.get("supplier_price")),
        shipment_reference=tracking_information.get("master_tracking_number"),
    )


def _extract_shipments(details: dict[str, Any]) -> list[Shipment]:
    shipments: list[Shipment] = []
    seen: set[tuple[str | None, str | None]] = set()

    for line in details.get("lines", []):
        for raw_pol in line.get("purchase_order_lines", []):
            tracking_information = (
                (raw_pol.get("shipping_information") or {})
                .get("tracking_information")
                or {}
            )
            if not tracking_information:
                continue

            for shipment in _normalize_tracking_information(tracking_information):
                key = (shipment.carrier, shipment.tracking_number)
                if key not in seen:
                    seen.add(key)
                    shipments.append(shipment)

    return shipments


def _normalize_tracking_information(raw_tracking: dict[str, Any]) -> list[Shipment]:
    master_tracking_number = raw_tracking.get("master_tracking_number")
    child_tracking_numbers = raw_tracking.get("child_tracking_numbers") or []
    tracking_statuses = raw_tracking.get("tracking_status") or {}
    carrier = raw_tracking.get("carrier")
    shipments: list[Shipment] = []

    if tracking_statuses:
        for status_key, status_payload in tracking_statuses.items():
            tracking_number = status_payload.get("tracking_number") or status_key
            shipments.append(
                Shipment(
                    carrier=carrier,
                    tracking_number=tracking_number,
                    child_tracking_numbers=(
                        child_tracking_numbers
                        if tracking_number == master_tracking_number
                        else []
                    ),
                    tracking_status=status_payload.get("status"),
                    tracking_description=status_payload.get("description"),
                    raw_status_code=status_payload.get("status_code"),
                    eta_start=status_payload.get("estimated_delivery_window_begins") or None,
                    eta_end=status_payload.get("estimated_delivery_window_ends") or None,
                    ship_date=status_payload.get("ship_date") or None,
                    actual_pickup_date=status_payload.get("actual_pickup_date") or None,
                    first_scan_date=status_payload.get("first_scan_date") or None,
                    delivered_at=status_payload.get("delivery_date") or None,
                    tracking_status_source="embedded_expand",
                )
            )
        return shipments

    return [
        Shipment(
            carrier=carrier,
            tracking_number=master_tracking_number,
            child_tracking_numbers=child_tracking_numbers,
            tracking_status_source="not_available",
        )
    ]


def redact_secret(url: str | None) -> str | None:
    if url is None:
        return None
    return SECRET_KEY_PATTERN.sub(r"\1***", url)


def _to_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    return float(value)


def _to_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    return int(value)

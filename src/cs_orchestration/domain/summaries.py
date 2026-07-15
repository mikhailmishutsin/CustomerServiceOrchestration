from cs_orchestration.domain.models import HelpdeskRequest, Order, SupportSummary
from cs_orchestration.presentation.formatting import (
    display_delivery_status,
    display_eta,
    format_datetime,
)


def build_support_summary(request: HelpdeskRequest, orders: list[Order]) -> SupportSummary:
    if not orders:
        return SupportSummary(
            short_summary="No matching WISMO orders found.",
            private_note=(
                "No orders were found in the last 30 days for the provided "
                "phone/email/name/order reference."
            ),
            confidence="low",
            warnings=["No matching OMS orders were found in the last 30 days."],
        )

    latest = orders[0]
    shipment = latest.shipments[0] if latest.shipments else None
    latest_line = _latest_line(latest, shipment)
    latest_eta = display_eta(shipment)
    latest_status = display_delivery_status(shipment)

    note_lines = [
        (
            f"Found {len(orders)} order(s) in the last 30 days "
            f"for ticket {request.ticket_id}."
        ),
        latest_line + ".",
    ]
    note_lines.extend(
        [
            "",
            "Recent orders:",
        ]
    )
    for index, order in enumerate(orders, start=1):
        prefix = "Latest" if index == 1 else f"Order {index}"
        order_shipment = _shipment_text(order.shipments[0] if order.shipments else None)
        line = (
            f"- {prefix}: {order.order_number}"
            f" | Order date: {format_datetime(order.order_date) or 'unknown'}"
            f" | Status: {order.order_status or 'unknown'}"
            f" | Fulfillment: {order.fulfillment_status or 'unknown'}"
        )
        if order_shipment:
            line = f"{line} | Shipment: {order_shipment}"
        note_lines.append(line)
    latest_tracking_lines = _latest_order_tracking_lines(latest)
    if latest_tracking_lines:
        note_lines.extend(["", "Latest order tracking details:"])
        note_lines.extend(latest_tracking_lines)

    warnings = []
    if any(
        shipment.tracking_status_source == "not_available"
        for order in orders
        for shipment in order.shipments
    ):
        warnings.append("Some shipments have tracking references but no current tracking status.")

    return SupportSummary(
        short_summary=_short_summary(
            order_number=latest.order_number,
            order_date=latest.order_date,
            delivery_status=latest_status,
            eta=latest_eta,
        ),
        private_note="\n".join(note_lines),
        latest_order_link=latest.details_ref.safe_agent_url if latest.details_ref else None,
        latest_delivery_status=latest_status,
        latest_delivery_eta=latest_eta,
        latest_order_date=format_datetime(latest.order_date),
        confidence="high" if latest.shipments else "medium",
        warnings=warnings,
    )


def _shipment_text(shipment: object | None) -> str | None:
    if shipment is None:
        return None

    carrier = getattr(shipment, "carrier", None)
    status = display_delivery_status(shipment)
    eta = display_eta(shipment)
    pieces = []
    if carrier:
        pieces.append(carrier)
    if status:
        pieces.append(f"Delivery status: {status}")
    if eta:
        pieces.append(f"ETA: {eta}")
    return " ".join(pieces) if pieces else None


def _latest_order_tracking_lines(order: Order) -> list[str]:
    lines: list[str] = []
    for index, shipment in enumerate(order.shipments, start=1):
        pieces = [f"- Tracking {index}"]
        tracking_number = getattr(shipment, "tracking_number", None)
        if tracking_number:
            pieces.append(f"Number: {tracking_number}")
        carrier = getattr(shipment, "carrier", None)
        if carrier:
            pieces.append(f"Carrier: {carrier}")
        status = display_delivery_status(shipment)
        if status:
            pieces.append(f"Status: {status}")
        tracking_details = getattr(shipment, "tracking_description", None)
        if tracking_details and tracking_details != status:
            pieces.append(f"Details: {tracking_details}")
        eta = display_eta(shipment)
        if eta:
            pieces.append(f"ETA: {eta}")
        first_scan = format_datetime(getattr(shipment, "first_scan_date", None))
        if first_scan:
            pieces.append(f"First FedEx scan: {first_scan}")
        delivered_at = format_datetime(getattr(shipment, "delivered_at", None))
        if delivered_at:
            pieces.append(f"Delivered: {delivered_at}")
        child_tracking_numbers = getattr(shipment, "child_tracking_numbers", [])
        if child_tracking_numbers:
            pieces.append(
                "Child tracking numbers: " + ", ".join(child_tracking_numbers)
            )
        lines.append(" | ".join(pieces))
    return lines


def _latest_line(order: Order, shipment: object | None) -> str:
    parts = [
        f"Latest order {order.order_number}",
    ]
    order_date = format_datetime(order.order_date)
    if order_date:
        parts.append(f"placed {order_date}")

    delivery_status = display_delivery_status(shipment)
    if delivery_status:
        parts.append(f"delivery status {delivery_status}")
    else:
        parts.append(
            f"fulfillment {order.fulfillment_status or order.order_status or 'Status unavailable'}"
        )

    eta = display_eta(shipment)
    if eta:
        parts.append(f"ETA {eta}")

    return ", ".join(parts)


def _short_summary(
    *,
    order_number: str,
    order_date: str | None,
    delivery_status: str | None,
    eta: str | None,
) -> str:
    pieces = [f"Latest order {order_number}"]
    formatted_order_date = format_datetime(order_date)
    if formatted_order_date:
        pieces.append(f"placed {formatted_order_date}")
    if delivery_status:
        pieces.append(f"Delivery status: {delivery_status}")
    if eta:
        pieces.append(f"ETA: {eta}")
    return " | ".join(pieces) + "."

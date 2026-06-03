from cs_orchestration.domain.models import HelpdeskRequest, Order, SupportSummary


def build_support_summary(request: HelpdeskRequest, orders: list[Order]) -> SupportSummary:
    if not orders:
        return SupportSummary(
            short_summary="No matching orders found.",
            private_note="No matching orders found by provided phone/email/name/order reference.",
            confidence="low",
            warnings=["No matching OMS orders were found."],
        )

    latest = orders[0]
    shipment = latest.shipments[0] if latest.shipments else None
    shipment_text = _shipment_text(shipment)
    latest_line = (
        f"Latest order {latest.order_number}: "
        f"{latest.fulfillment_status or latest.order_status or 'Status unavailable'}"
    )
    if shipment_text:
        latest_line = f"{latest_line}, {shipment_text}"

    note_lines = [
        f"Found {len(orders)} recent order(s) for ticket {request.ticket_id}.",
        latest_line + ".",
        "",
        "Recent orders:",
    ]
    for index, order in enumerate(orders, start=1):
        prefix = "Latest" if index == 1 else f"Order {index}"
        order_shipment = _shipment_text(order.shipments[0] if order.shipments else None)
        line = (
            f"- {prefix}: {order.order_number}"
            f" | Date: {order.order_date or 'unknown'}"
            f" | Status: {order.order_status or 'unknown'}"
            f" | Fulfillment: {order.fulfillment_status or 'unknown'}"
        )
        if order_shipment:
            line = f"{line} | Shipment: {order_shipment}"
        note_lines.append(line)

    warnings = []
    if any(
        shipment.tracking_status_source == "not_available"
        for order in orders
        for shipment in order.shipments
    ):
        warnings.append("Some shipments have tracking references but no current tracking status.")

    return SupportSummary(
        short_summary=latest_line + ".",
        private_note="\n".join(note_lines),
        latest_order_link=latest.details_ref.safe_agent_url if latest.details_ref else None,
        confidence="high" if latest.shipments else "medium",
        warnings=warnings,
    )


def _shipment_text(shipment: object | None) -> str | None:
    if shipment is None:
        return None

    carrier = getattr(shipment, "carrier", None)
    status = getattr(shipment, "tracking_status", None)
    eta_end = getattr(shipment, "eta_end", None)
    pieces = [piece for piece in [carrier, status] if piece]
    if eta_end:
        pieces.append(f"ETA {eta_end}")
    return " ".join(pieces) if pieces else None

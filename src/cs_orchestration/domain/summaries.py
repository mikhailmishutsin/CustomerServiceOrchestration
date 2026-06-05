from datetime import UTC, datetime, timedelta

from cs_orchestration.domain.models import HelpdeskRequest, Order, SupportSummary


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
    latest_eta = _display_eta(shipment)
    latest_status = _display_delivery_status(shipment)

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
            f" | Order date: {_format_datetime(order.order_date) or 'unknown'}"
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
        latest_order_date=_format_datetime(latest.order_date),
        confidence="high" if latest.shipments else "medium",
        warnings=warnings,
    )


def _shipment_text(shipment: object | None) -> str | None:
    if shipment is None:
        return None

    carrier = getattr(shipment, "carrier", None)
    status = _display_delivery_status(shipment)
    eta = _display_eta(shipment)
    pieces = []
    if carrier:
        pieces.append(carrier)
    if status:
        pieces.append(f"Delivery status: {status}")
    if eta:
        pieces.append(f"ETA: {eta}")
    return " ".join(pieces) if pieces else None


def _latest_line(order: Order, shipment: object | None) -> str:
    parts = [
        f"Latest order {order.order_number}",
    ]
    order_date = _format_datetime(order.order_date)
    if order_date:
        parts.append(f"placed {order_date}")

    delivery_status = _display_delivery_status(shipment)
    if delivery_status:
        parts.append(f"delivery status {delivery_status}")
    else:
        parts.append(
            f"fulfillment {order.fulfillment_status or order.order_status or 'Status unavailable'}"
        )

    eta = _display_eta(shipment)
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
    formatted_order_date = _format_datetime(order_date)
    if formatted_order_date:
        pieces.append(f"placed {formatted_order_date}")
    if delivery_status:
        pieces.append(f"Delivery status: {delivery_status}")
    if eta:
        pieces.append(f"ETA: {eta}")
    return " | ".join(pieces) + "."


def _display_delivery_status(shipment: object | None) -> str | None:
    if shipment is None:
        return None
    return getattr(shipment, "tracking_status", None) or getattr(
        shipment, "tracking_description", None
    )


def _display_eta(shipment: object | None) -> str | None:
    if shipment is None:
        return None
    return _format_datetime_range(
        getattr(shipment, "eta_start", None),
        getattr(shipment, "eta_end", None),
    )


def _format_datetime(value: str | None) -> str | None:
    if not value:
        return None

    dt = _parse_datetime(value)
    if dt is None:
        return value

    return f"{dt.strftime('%b %d, %Y')}, {_format_time(dt)} {_tz_label(dt)}"


def _format_datetime_range(start: str | None, end: str | None) -> str | None:
    start_dt = _parse_datetime(start)
    end_dt = _parse_datetime(end)
    if start_dt and end_dt:
        if _tz_label(start_dt) == _tz_label(end_dt) and start_dt.date() == end_dt.date():
            return (
                f"{start_dt.strftime('%b %d, %Y')}, "
                f"{_format_time(start_dt)} - {_format_time(end_dt)} {_tz_label(end_dt)}"
            )
        return f"{_format_datetime(start)} to {_format_datetime(end)}"
    if end_dt:
        return _format_datetime(end)
    if start_dt:
        return _format_datetime(start)
    return None


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    normalized = value.strip()
    if not normalized:
        return None
    if normalized.endswith("Z"):
        normalized = normalized[:-1] + "+00:00"

    try:
        dt = datetime.fromisoformat(normalized)
    except ValueError:
        return None

    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt


def _format_time(dt: datetime) -> str:
    hour = dt.strftime("%I").lstrip("0") or "0"
    return f"{hour}:{dt.strftime('%M')} {dt.strftime('%p')}"


def _tz_label(dt: datetime) -> str:
    offset = dt.utcoffset()
    if offset in (None, timedelta(0)):
        return "UTC"
    if offset in (timedelta(hours=-4), timedelta(hours=-5)):
        return "ET"
    total_minutes = int(offset.total_seconds() // 60)
    sign = "+" if total_minutes >= 0 else "-"
    absolute_minutes = abs(total_minutes)
    hours, minutes = divmod(absolute_minutes, 60)
    return f"UTC{sign}{hours:02d}:{minutes:02d}"

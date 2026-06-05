from html import escape
from typing import Any

from cs_orchestration.domain.models import HelpdeskUpdate


def render_freshdesk_private_note(update: HelpdeskUpdate) -> str:
    orders = update.metadata.get("matched_orders") or []
    if not orders:
        return _fallback_note_html(update)

    latest_order = orders[0]
    other_orders = orders[1:]
    sections = [
        '<div style="font-family: Arial, sans-serif; font-size: 13px; line-height: 1.38;">',
        '<div style="font-weight: 700; font-size: 15px; margin-bottom: 8px;">Order context</div>',
        _match_notice(update),
        _latest_order_section(latest_order),
        _tracking_section(latest_order),
    ]
    if other_orders:
        sections.append(_other_orders_section(other_orders))
    sections.append("</div>")
    return "".join(section for section in sections if section)


def _fallback_note_html(update: HelpdeskUpdate) -> str:
    note_html = _plain_text_to_html(update.private_note)
    order_link = update.custom_fields.get("order_link")
    if order_link:
        safe_url = _safe_text(order_link)
        note_html = (
            f"{note_html}"
            "<br /><br />"
            f'Sales order: <a href="{safe_url}" target="_blank" rel="noopener noreferrer">Open in OMS</a>'
        )
    return f"<div>{note_html}</div>"


def _match_notice(update: HelpdeskUpdate) -> str:
    match_quality = update.metadata.get("match_quality")
    if match_quality != "partial_contact_match":
        return ""

    details = update.metadata.get("contact_match_details") or {}
    matched_on = _humanize_fields(details.get("matched_on") or [])
    mismatched_on = _humanize_fields(details.get("mismatched_on") or [])
    return (
        '<div style="padding: 8px 10px; margin: 8px 0 10px; '
        'border-left: 4px solid #d97706; background: #fff7ed;">'
        "<strong>No exact contact match found.</strong><br />"
        f"Partial match: matched on {_safe_text(matched_on)}, "
        f"did not match on {_safe_text(mismatched_on)}."
        "</div>"
    )


def _latest_order_section(order: dict[str, Any]) -> str:
    customer = order.get("customer") or {}
    order_reference = _safe_text(_order_reference(order))
    order_reference_html = order_reference
    order_link = order.get("order_link")
    if order_link:
        safe_url = _safe_text(order_link)
        order_reference_html = (
            f'<a href="{safe_url}" target="_blank" rel="noopener noreferrer">{order_reference}</a>'
        )

    details = [
        f"<strong>Date:</strong> {_safe_text(order.get('order_date'))}"
        if order.get("order_date")
        else None,
        f"<strong>Marketplace:</strong> {_safe_text(order.get('marketplace'))}"
        if order.get("marketplace")
        else None,
        f"<strong>Customer:</strong> {_safe_text(_customer_text(customer))}"
        if _customer_text(customer)
        else None,
    ]
    return (
        '<div style="margin: 6px 0 10px;">'
        f"<div><strong>Latest order:</strong> {order_reference_html}</div>"
        f'<div style="margin-top: 3px;">{" &nbsp; ".join(item for item in details if item)}</div>'
        "</div>"
    )


def _tracking_section(order: dict[str, Any]) -> str:
    shipments = order.get("shipments") or []
    if not shipments:
        return (
            '<div style="margin: 8px 0;"><strong>Tracking:</strong> '
            "No shipment tracking details available.</div>"
        )

    lines = []
    for index, shipment in enumerate(shipments, start=1):
        tracking_number = shipment.get("tracking_number")
        tracking_url = shipment.get("tracking_url")
        if tracking_number and tracking_url:
            tracking_value = (
                f'<a href="{_safe_text(tracking_url)}" target="_blank" '
                f'rel="noopener noreferrer">{_safe_text(tracking_number)}</a>'
            )
        else:
            tracking_value = _safe_text(tracking_number or "unknown")

        details = [
            _safe_text(shipment.get("carrier")) if shipment.get("carrier") else None,
            f"Status: {_safe_text(shipment.get('tracking_status'))}"
            if shipment.get("tracking_status")
            else None,
            f"Details: {_safe_text(shipment.get('tracking_details'))}"
            if shipment.get("tracking_details")
            and shipment.get("tracking_details") != shipment.get("tracking_status")
            else None,
            f"ETA: {_safe_text(shipment.get('eta'))}" if shipment.get("eta") else None,
            f"First scan: {_safe_text(shipment.get('first_scan_date'))}"
            if shipment.get("first_scan_date")
            else None,
            f"Delivered: {_safe_text(shipment.get('delivered_at'))}"
            if shipment.get("delivered_at")
            else None,
            "Child tracking: "
            + _safe_text(", ".join(shipment.get("child_tracking_numbers") or []))
            if shipment.get("child_tracking_numbers")
            else None,
        ]
        label = "Tracking" if len(shipments) == 1 else f"Tracking {index}"
        lines.append(
            '<div style="margin: 3px 0;">'
            f"<strong>{_safe_text(label)}:</strong> {tracking_value}"
            f'<span style="margin-left: 8px;">{" &nbsp; ".join(item for item in details if item)}</span>'
            "</div>"
        )
    return (
        '<div style="margin: 8px 0 12px;">'
        '<div style="font-weight: 700; margin-bottom: 3px;">Tracking</div>'
        + "".join(lines)
        + "</div>"
    )


def _other_orders_section(orders: list[dict[str, Any]]) -> str:
    rows = []
    for order in orders:
        shipments = order.get("shipments") or []
        shipment = shipments[0] if shipments else {}
        status = shipment.get("tracking_status") or shipment.get("tracking_details")
        rows.append(
            "<tr>"
            f"<td style=\"padding: 5px 10px 5px 0;\">{_safe_text(_order_reference(order))}</td>"
            f"<td style=\"padding: 5px 10px;\">{_safe_text(order.get('order_date') or 'unknown')}</td>"
            f"<td style=\"padding: 5px 10px;\">{_safe_text(order.get('marketplace') or 'unknown')}</td>"
            f"<td style=\"padding: 5px 0 5px 10px;\">{_safe_text(status or 'unknown')}</td>"
            "</tr>"
        )
    return (
        '<div style="font-weight: 700; margin: 10px 0 4px;">Other recent orders</div>'
        + '<table style="border-collapse: collapse; font-size: 13px;">'
        + '<thead><tr><th style="text-align: left; padding-right: 10px;">SO</th>'
        + '<th style="text-align: left; padding: 0 10px;">Date</th>'
        + '<th style="text-align: left; padding: 0 10px;">Marketplace</th>'
        + '<th style="text-align: left; padding-left: 10px;">Status</th>'
        + "</tr></thead><tbody>"
        + "".join(rows)
        + "</tbody></table>"
    )


def _customer_text(customer: dict[str, Any]) -> str | None:
    pieces = [
        customer.get("name"),
        customer.get("email"),
        customer.get("phone"),
    ]
    present = [str(piece) for piece in pieces if piece]
    return " | ".join(present) if present else None


def _order_reference(order: dict[str, Any]) -> str:
    return str(order.get("order_reference") or "unknown")


def _humanize_fields(fields: list[str]) -> str:
    labels = {
        "customer_phone": "phone",
        "customer_email": "email",
    }
    readable = [labels.get(field, field) for field in fields]
    if not readable:
        return "none"
    if len(readable) == 1:
        return readable[0]
    return " and ".join(readable)


def _plain_text_to_html(text: str) -> str:
    return escape(text).replace("\n", "<br />")


def _safe_text(value: object) -> str:
    return escape(str(value), quote=True)

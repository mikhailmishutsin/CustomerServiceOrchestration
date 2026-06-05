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
        '<div style="font-family: Arial, sans-serif; font-size: 14px; line-height: 1.45;">',
        _heading("Order enrichment result"),
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
        '<div style="padding: 10px 12px; margin: 10px 0 14px; '
        'border-left: 4px solid #d97706; background: #fff7ed;">'
        "<strong>No exact contact match found.</strong><br />"
        f"Partial match: matched on {_safe_text(matched_on)}, "
        f"did not match on {_safe_text(mismatched_on)}."
        "</div>"
    )


def _latest_order_section(order: dict[str, Any]) -> str:
    customer = order.get("customer") or {}
    rows = [
        ("SO", _order_reference(order)),
        ("Order date", order.get("order_date")),
        ("Marketplace", order.get("marketplace")),
        ("Customer", _customer_text(customer)),
    ]
    order_link = order.get("order_link")
    if order_link:
        safe_url = _safe_text(order_link)
        rows.append(
            (
                "Sales Order",
                f'<a href="{safe_url}" target="_blank" rel="noopener noreferrer">Open in OMS</a>',
            )
        )
    return (
        _heading("Latest order")
        + '<table style="border-collapse: collapse; margin-bottom: 14px;">'
        + "".join(_table_row(label, value) for label, value in rows if value)
        + "</table>"
    )


def _tracking_section(order: dict[str, Any]) -> str:
    shipments = order.get("shipments") or []
    if not shipments:
        return _heading("Tracking") + "<p>No shipment tracking details available.</p>"

    cards = []
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

        rows = [
            ("Tracking number", tracking_value),
            ("Carrier", shipment.get("carrier")),
            ("Status", shipment.get("tracking_status")),
            ("Details", shipment.get("tracking_details")),
            ("ETA", shipment.get("eta")),
            ("First FedEx scan", shipment.get("first_scan_date")),
            ("Delivered", shipment.get("delivered_at")),
            (
                "Child tracking numbers",
                ", ".join(shipment.get("child_tracking_numbers") or []),
            ),
        ]
        cards.append(
            '<div style="border: 1px solid #ddd; border-radius: 6px; '
            'padding: 10px 12px; margin: 8px 0;">'
            f"<strong>Tracking {index}</strong>"
            '<table style="border-collapse: collapse; margin-top: 6px;">'
            + "".join(_table_row(label, value) for label, value in rows if value)
            + "</table>"
            "</div>"
        )
    return _heading("Tracking") + "".join(cards)


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
        _heading("Other recent orders")
        + '<table style="border-collapse: collapse;">'
        + '<thead><tr><th style="text-align: left; padding-right: 10px;">SO</th>'
        + '<th style="text-align: left; padding: 0 10px;">Order date</th>'
        + '<th style="text-align: left; padding: 0 10px;">Marketplace</th>'
        + '<th style="text-align: left; padding-left: 10px;">Shipment status</th>'
        + "</tr></thead><tbody>"
        + "".join(rows)
        + "</tbody></table>"
    )


def _heading(text: str) -> str:
    return f'<h3 style="margin: 14px 0 8px;">{_safe_text(text)}</h3>'


def _table_row(label: str, value: object) -> str:
    return (
        "<tr>"
        f'<td style="font-weight: 600; padding: 3px 14px 3px 0;">{_safe_text(label)}</td>'
        f'<td style="padding: 3px 0;">{value if _looks_like_html(value) else _safe_text(value)}</td>'
        "</tr>"
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


def _looks_like_html(value: object) -> bool:
    return isinstance(value, str) and value.startswith("<a ")

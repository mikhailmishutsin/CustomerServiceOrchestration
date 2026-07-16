import httpx

from cs_orchestration.domain.models import HelpdeskUpdate
from cs_orchestration.integrations.helpdesk.freshdesk_adapter import FreshdeskAdapter


def test_freshdesk_adapter_posts_private_note_and_returns_metadata() -> None:
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["method"] = request.method
        captured["url"] = str(request.url)
        captured["auth"] = request.headers.get("authorization")
        captured["content_type"] = request.headers.get("content-type")
        captured["body"] = request.content.decode("utf-8")
        return httpx.Response(
            201,
            json={
                "id": 98765,
                "ticket_id": 12345,
                "private": True,
            },
        )

    adapter = FreshdeskAdapter(
        base_url="https://example.freshdesk.com",
        api_key="freshdesk-key",
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    update = adapter.apply_update(
        HelpdeskUpdate(
            ticket_id="12345",
            private_note="Line one\nLine two",
            custom_fields={
                "order_link": "https://ds.utires.com/order_management/#order=wlm-123"
            },
            metadata={"operation": "recent_orders_by_contact_or_reference"},
        )
    )

    assert captured["method"] == "POST"
    assert captured["url"] == "https://example.freshdesk.com/api/v2/tickets/12345/notes"
    assert captured["auth"] == "Basic ZnJlc2hkZXNrLWtleTpY"
    assert captured["content_type"] == "application/json"
    assert '"private":true' in str(captured["body"]).replace(" ", "")
    assert "&lt;" not in str(captured["body"])
    assert "<br />" in str(captured["body"])
    assert "Sales order:" in str(captured["body"])
    assert (
        'href=\\"https://ds.utires.com/order_management/#order=wlm-123\\"'
        in str(captured["body"])
    )
    assert "https://ds.utires.com/order_management/#order=wlm-123" in str(captured["body"])
    assert update.metadata["freshdesk"]["note_id"] == 98765
    assert update.metadata["freshdesk"]["ticket_id"] == 12345
    assert update.metadata["freshdesk"]["private"] is True
    assert update.metadata["freshdesk"]["status_code"] == 201


def test_freshdesk_adapter_renders_structured_latest_order_note() -> None:
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["body"] = request.content.decode("utf-8")
        return httpx.Response(
            201,
            json={
                "id": 98765,
                "ticket_id": 12345,
                "private": True,
            },
        )

    adapter = FreshdeskAdapter(
        base_url="https://example.freshdesk.com",
        api_key="freshdesk-key",
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    adapter.apply_update(
        HelpdeskUpdate(
            ticket_id="12345",
            private_note="Plain fallback note should not drive structured rendering",
            metadata={
                "match_quality": "exact_contact_match",
                "matched_orders": [
                    {
                        "order_reference": "wlm-latest",
                        "order_date": "Jun 01, 2026, 10:00 AM CDT",
                        "ship_by": "Jun 02, 2026, 5:00 PM CDT",
                        "deliver_by": "Jun 05, 2026, 5:00 PM CDT",
                        "marketplace": "walmart_main",
                        "customer": {
                            "name": "John Customer",
                            "email": "customer@example.com",
                            "phone": "5551234567",
                        },
                        "order_link": "https://ds.utires.com/order_management/#order=wlm-latest",
                        "shipments": [
                            {
                                "carrier": "FedEx",
                                "tracking_number": "999999999999",
                                "tracking_url": "https://www.fedex.com/fedextrack/?trknbr=999999999999",
                                "tracking_status": "Delivered",
                                "tracking_details": "Delivered",
                                "eta": "Jun 03, 2026, 9:00 AM - 5:00 PM CDT",
                                "actual_pickup_date": "Jun 02, 2026, 1:34 PM CDT",
                                "delivered_at": "Jun 03, 2026, 2:12 PM CDT",
                                "child_tracking_numbers": [],
                            }
                        ],
                    },
                    {
                        "order_reference": "wlm-older",
                        "order_date": "May 28, 2026, 2:00 PM CDT",
                        "marketplace": "ebay",
                        "customer": {},
                        "order_link": "https://ds.utires.com/order_management/#order=wlm-older",
                        "shipments": [
                            {
                                "tracking_status": "In transit",
                            }
                        ],
                    },
                ],
            },
        )
    )

    body = str(captured["body"])
    assert "Order context" in body
    assert "Latest order:" in body
    assert "Order dates" in body
    assert "Order date:</strong> Jun 01, 2026, 10:00 AM CDT" in body
    assert "Ship by:</strong> Jun 02, 2026, 5:00 PM CDT" in body
    assert "Deliver by:</strong> Jun 05, 2026, 5:00 PM CDT" in body
    assert "OMS link:" in body
    assert "Tracking" in body
    assert "Tracking 1:" not in body
    assert "Actual pickup: Jun 02, 2026, 1:34 PM CDT" in body
    assert "First scan:" not in body
    assert "Other recent orders" in body
    assert ">https://ds.utires.com/order_management/#order=wlm-latest</a>" in body
    assert (
        'href=\\"https://ds.utires.com/order_management/#order=wlm-latest\\"'
        in body
    )
    assert "https://ds.utires.com/order_management/#order=wlm-latest" in body
    assert "https://www.fedex.com/fedextrack/?trknbr=999999999999" in body
    assert body.index("wlm-latest") < body.index("Order dates")
    assert body.index("Order dates") < body.index("Tracking")
    assert body.index("Tracking") < body.index("Other recent orders")
    other_orders_html = body[body.index("Other recent orders"):]
    assert "wlm-latest" not in other_orders_html
    assert "wlm-older" in body

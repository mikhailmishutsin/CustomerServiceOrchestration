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
    assert update.metadata["freshdesk"]["note_id"] == 98765
    assert update.metadata["freshdesk"]["ticket_id"] == 12345
    assert update.metadata["freshdesk"]["private"] is True
    assert update.metadata["freshdesk"]["status_code"] == 201

from fastapi.testclient import TestClient

from cs_orchestration.main import app


def test_enrich_ticket_endpoint_returns_dry_run_update() -> None:
    client = TestClient(app)

    response = client.post(
        "/enrich-ticket",
        json={
            "ticket_id": "12345",
            "customer": {
                "name": "John Customer",
                "email": "customer@example.com",
                "phone": "+15555555555",
            },
            "ticket": {
                "subject": "Where is my order?",
                "description": "I need an update on delivery",
                "source": "email",
                "channel": "freshdesk",
            },
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["ticket_id"] == "12345"
    assert body["metadata"]["dry_run"] is True
    assert body["metadata"]["order_count"] == 1
    assert "Delivered" in body["private_note"]

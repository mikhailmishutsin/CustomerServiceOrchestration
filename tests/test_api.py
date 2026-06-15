from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

import cs_orchestration.api.routes.enrichment as enrichment_routes
from cs_orchestration.config.settings import settings
from cs_orchestration.integrations.helpdesk.freshdesk_adapter import FreshdeskAdapter
from cs_orchestration.integrations.oms.factory import build_order_business_client
from cs_orchestration.main import app, create_app
from cs_orchestration.ui import render_agent_preview
from cs_orchestration.workflows.enrich_ticket import EnrichTicketWithOrdersWorkflow


@pytest.fixture(autouse=True)
def force_mock_mode_for_api_tests(monkeypatch: pytest.MonkeyPatch) -> None:
    original_app_env = settings.app_env
    original_mode = settings.integration_mode
    original_inbound_api_key = settings.inbound_api_key
    original_dry_run = settings.dry_run
    original_expose_docs = settings.expose_docs
    original_expose_debug_errors = settings.expose_debug_errors
    original_freshdesk_base_url = settings.freshdesk.base_url
    original_freshdesk_api_key = settings.freshdesk.api_key
    settings.app_env = "local"
    settings.integration_mode = "mock"
    settings.inbound_api_key = None
    settings.dry_run = True
    settings.expose_docs = True
    settings.expose_debug_errors = True
    monkeypatch.setattr(enrichment_routes, "_workflow", _fixed_clock_workflow)
    yield
    settings.app_env = original_app_env
    settings.integration_mode = original_mode
    settings.inbound_api_key = original_inbound_api_key
    settings.dry_run = original_dry_run
    settings.expose_docs = original_expose_docs
    settings.expose_debug_errors = original_expose_debug_errors
    settings.freshdesk.base_url = original_freshdesk_base_url
    settings.freshdesk.api_key = original_freshdesk_api_key


def _fixed_clock_workflow() -> EnrichTicketWithOrdersWorkflow:
    helpdesk_adapter = None
    if settings.freshdesk.base_url and settings.freshdesk.api_key:
        helpdesk_adapter = FreshdeskAdapter(
            base_url=settings.freshdesk.base_url,
            api_key=settings.freshdesk.api_key,
        )
    return EnrichTicketWithOrdersWorkflow(
        oms_client=build_order_business_client(settings),
        helpdesk_adapter=helpdesk_adapter,
        order_management_base_url=settings.order_management_base_url,
        now_provider=lambda: datetime(2026, 6, 4, tzinfo=UTC),
    )


def test_agent_preview_ui_loads() -> None:
    client = TestClient(app)

    response = client.get("/")

    assert response.status_code == 200
    assert "Customer Service Orchestration" in response.text
    assert "Enrich ticket" in response.text
    assert "Debug" in response.text
    assert "Mock OMS" in response.text


def test_agent_preview_real_mode_has_blank_ticket_fields() -> None:
    response = render_agent_preview(integration_mode="real", dry_run=True)
    html = response.body.decode("utf-8")

    assert "Real Order Business API" in html
    assert "John Customer" not in html
    assert "customer@example.com" not in html
    assert "+15555555555" not in html
    assert "Where is my order?" not in html
    assert "parseResponse" in html


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
    assert body["custom_fields"]["delivery_status"] == "Delivered"
    assert body["custom_fields"]["delivery_eta"] == "May 14, 2026, 8:00 PM ET"
    assert body["custom_fields"]["order_date"] == "May 12, 2026, 5:20 PM ET"
    assert (
        body["custom_fields"]["order_link"]
        == "https://ds.utires.com/order_management/#order=wlm-000000000000000"
    )


def test_generic_enrichment_endpoint_returns_structured_response() -> None:
    client = TestClient(app)

    response = client.post(
        "/enrichment/resolve",
        json={
            "source_system": "twilio",
            "source_record_id": "sms-001",
            "case_type": "WISMO",
            "lookup": {
                "order_reference": "wlm-000000000000000",
            },
            "ticket": {
                "source": "sms",
                "channel": "twilio",
            },
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["source_system"] == "twilio"
    assert body["source_record_id"] == "sms-001"
    assert body["case_type"] == "WISMO"
    assert body["normalized_case_type"] == "wismo"
    assert body["match_status"] == "single_match"
    assert body["matched_order_count"] == 1
    assert body["result"]["delivery_status"] == "Delivered"
    assert body["result"]["delivery_eta"] == "May 14, 2026, 8:00 PM ET"
    assert body["result"]["order_date"] == "May 12, 2026, 5:20 PM ET"
    assert body["result"]["order_link"] == (
        "https://ds.utires.com/order_management/#order=wlm-000000000000000"
    )
    assert body["metadata"]["lookup_used"]["customer_phone_normalized"] is None
    assert body["metadata"]["search_window_days"] == 30
    assert body["metadata"]["search_window_note"] == "WISMO checks orders placed within the last 30 days."
    assert body["matched_orders"][0]["marketplace"] == "walmart_main"
    assert body["matched_orders"][0]["customer"]["email"] == "customer@example.com"
    assert body["matched_orders"][0]["shipments"][0]["tracking_status"] == "Delivered"
    assert body["matched_orders"][0]["shipments"][0]["eta"] == "May 14, 2026, 8:00 PM ET"


def test_latest_order_by_contact_endpoint_returns_single_order() -> None:
    client = TestClient(app)

    response = client.post(
        "/orders/latest-by-contact",
        json={
            "source_system": "twilio",
            "case_type": "WISMO",
            "lookup": {
                "customer_phone": "+1 (555) 123-4567"
            },
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["metadata"]["operation"] == "latest_order_by_contact"
    assert body["matched_order_count"] == 1
    assert len(body["matched_orders"]) == 1
    assert body["metadata"]["returned_order_count"] == 1


def test_recent_orders_by_contact_endpoint_returns_recent_orders_payload() -> None:
    client = TestClient(app)

    response = client.post(
        "/orders/recent-by-contact",
        json={
            "source_system": "helpdesk",
            "case_type": "WISMO",
            "max_records": 7,
            "lookup": {
                "customer_email": "customer@example.com"
            },
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["metadata"]["operation"] == "recent_orders_by_contact"
    assert body["metadata"]["oms_max_records"] == 7
    assert body["matched_order_count"] == 1
    assert len(body["matched_orders"]) == 1


def test_freshdesk_recent_orders_endpoint_returns_helpdesk_update_shape() -> None:
    client = TestClient(app)

    response = client.post(
        "/freshdesk/recent-orders",
        json={
            "ticket_id": "fd-123",
            "customer_phone": "+1 (555) 123-4567",
            "customer_email": "customer@example.com",
            "order_number": "wlm-000000000000000",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["ticket_id"] == "fd-123"
    assert "Delivered" in body["private_note"]
    assert body["metadata"]["operation"] == "recent_orders_by_contact_or_reference"
    assert body["metadata"]["oms_max_records"] == 3
    assert body["metadata"]["dry_run"] is True
    assert body["custom_fields"]["delivery_status"] == "Delivered"


def test_generic_enrichment_endpoint_requires_lookup_input() -> None:
    client = TestClient(app)

    response = client.post(
        "/enrichment/resolve",
        json={
            "source_system": "helpdesk",
            "lookup": {},
        },
    )

    assert response.status_code == 400
    assert "At least one lookup field is required" in response.json()["detail"]["message"]


def test_config_status_does_not_expose_secret_values() -> None:
    client = TestClient(app)

    response = client.get("/config/status")

    assert response.status_code == 200
    body = response.json()
    assert "integration_mode" in body
    assert "dry_run" in body
    assert "inbound_api" in body
    assert "api_key_configured" in body["inbound_api"]
    assert "password_configured" in body["order_business_api"]
    assert "secret_key_configured" in body["order_business_api"]
    assert "freshdesk" in body
    assert "api_key_configured" in body["freshdesk"]
    assert "secret" not in body["order_business_api"]
    assert "secret" not in body["fedex_api"]


def test_production_app_hides_docs_preview_and_config_status() -> None:
    settings.app_env = "production"
    settings.expose_docs = False
    settings.expose_debug_errors = False
    settings.inbound_api_key = "test-inbound-key"
    client = TestClient(create_app(settings))

    assert client.get("/health").status_code == 200
    assert client.get("/docs").status_code == 404
    assert client.get("/openapi.json").status_code == 404
    assert client.get("/").status_code == 404
    assert client.get("/config/status").status_code == 404


def test_production_errors_do_not_include_debug_payloads() -> None:
    settings.app_env = "production"
    settings.expose_debug_errors = False
    settings.inbound_api_key = "test-inbound-key"
    client = TestClient(create_app(settings))

    response = client.post(
        "/enrichment/resolve",
        headers={"X-API-Key": "test-inbound-key"},
        json={
            "source_system": "helpdesk",
            "lookup": {},
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "At least one lookup field is required: order_reference, customer_phone, customer_email, or customer_name."
    )


def test_inbound_api_key_is_required_when_configured() -> None:
    client = TestClient(app)
    settings.inbound_api_key = "test-inbound-key"

    response = client.post(
        "/enrichment/resolve",
        json={
            "source_system": "twilio",
            "case_type": "WISMO",
            "lookup": {"customer_email": "customer@example.com"},
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Missing or invalid inbound API key."


def test_inbound_api_key_allows_request_when_present() -> None:
    client = TestClient(app)
    settings.inbound_api_key = "test-inbound-key"

    response = client.post(
        "/enrichment/resolve",
        headers={"X-API-Key": "test-inbound-key"},
        json={
            "source_system": "twilio",
            "case_type": "WISMO",
            "lookup": {"customer_email": "customer@example.com"},
        },
    )

    assert response.status_code == 200

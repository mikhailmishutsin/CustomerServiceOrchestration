from datetime import UTC, datetime
from pathlib import Path

from cs_orchestration.domain.models import (
    Customer,
    EnrichmentRequest,
    FreshdeskRecentOrdersRequest,
    HelpdeskRequest,
    LookupCriteria,
    TicketContext,
)
from cs_orchestration.integrations.helpdesk.mock_adapter import MockHelpdeskAdapter
from cs_orchestration.integrations.oms.mock_client import MockOmsClient
from cs_orchestration.workflows.enrich_ticket import EnrichTicketWithOrdersWorkflow


FIXTURE = Path("cs-orchestration-context/examples/oms-search-orders-response.json")


def test_workflow_returns_dry_run_helpdesk_update() -> None:
    request = HelpdeskRequest(
        ticket_id="12345",
        customer=Customer(
            name="John Customer",
            email="customer@example.com",
            phone="+15555555555",
        ),
        ticket=TicketContext(
            subject="Where is my order?",
            description="I need an update on delivery",
            source="email",
            channel="freshdesk",
        ),
    )
    oms_client = MockOmsClient(FIXTURE)
    workflow = EnrichTicketWithOrdersWorkflow(
        oms_client=oms_client,
        now_provider=lambda: datetime(2026, 6, 4, tzinfo=UTC),
    )

    update = workflow.run(request, dry_run=True)

    assert update.ticket_id == "12345"
    assert update.metadata["dry_run"] is True
    assert update.metadata["uses_expand"] is True
    assert update.metadata["order_count"] == 1
    assert "Latest order wlm-000000000000000" in update.custom_fields["order_summary"]
    assert update.custom_fields["delivery_status"] == "Delivered"
    assert update.custom_fields["delivery_eta"] == "May 14, 2026, 8:00 PM ET"
    assert update.custom_fields["order_date"] == "May 12, 2026, 5:20 PM ET"
    assert (
        update.custom_fields["order_link"]
        == "https://ds.utires.com/order_management/#order=wlm-000000000000000"
    )
    assert "Delivered" in update.private_note
    assert "Latest order tracking details:" in update.private_note
    assert "Tracking 1" in update.private_note
    assert "Number: 999999999999" in update.private_note
    assert "Carrier: FedEx" in update.private_note
    assert "First FedEx scan: May 15, 2026, 1:34 PM ET" in update.private_note
    assert oms_client.last_request["expand"] is True
    assert update.metadata["debug"]["order_business_request"]["operation"] == "search_orders"
    assert update.metadata["normalized_case_type"] == "wismo"
    assert update.metadata["search_window_days"] == 30
    assert update.metadata["search_window_note"] == "WISMO checks orders placed within the last 30 days."


def test_filter_mode_is_optional() -> None:
    request = HelpdeskRequest(
        ticket_id="12345",
        customer=Customer(phone="+15555555555"),
        ticket=TicketContext(channel="freshdesk"),
    )
    oms_client = MockOmsClient(FIXTURE)
    workflow = EnrichTicketWithOrdersWorkflow(
        oms_client=oms_client,
        now_provider=lambda: datetime(2026, 6, 4, tzinfo=UTC),
    )

    workflow.run(request)

    assert oms_client.last_request["filter_mode"] is None


def test_contact_lookup_runs_before_order_reference() -> None:
    oms_client = MockOmsClient(FIXTURE)
    workflow = EnrichTicketWithOrdersWorkflow(
        oms_client=oms_client,
        now_provider=lambda: datetime(2026, 6, 4, tzinfo=UTC),
    )

    response = workflow.run_enrichment_request(
        EnrichmentRequest(
            source_system="helpdesk",
            case_type="WISMO",
            lookup=LookupCriteria(
                customer_phone="+15555555555",
                customer_email="customer@example.com",
                order_reference="wlm-000000000000000",
            ),
        )
    )

    assert response.metadata["matched_by"] == "contact_exact"
    assert response.metadata["lookup_attempts"][0]["stage"] == "contact_exact"
    assert response.metadata["lookup_attempts"][0]["used"]["customer_phone"] == "5555555555"
    assert response.metadata["lookup_attempts"][0]["used"]["customer_email"] == "customer@example.com"
    assert response.metadata["lookup_attempts"][0]["used"]["filter_mode"] == "all"
    assert len(oms_client.request_history) == 1
    assert oms_client.request_history[0]["order_number"] is None
    assert response.metadata["lookup_used"]["customer_phone"] == "+15555555555"
    assert response.metadata["lookup_used"]["customer_phone_normalized"] == "5555555555"
    assert response.match_status == "single_match"
    assert response.metadata["match_quality"] == "exact_contact_match"
    assert response.metadata["exact_contact_match_found"] is True


def test_phone_is_normalized_for_oms_lookup() -> None:
    oms_client = MockOmsClient(FIXTURE)
    workflow = EnrichTicketWithOrdersWorkflow(
        oms_client=oms_client,
        now_provider=lambda: datetime(2026, 6, 4, tzinfo=UTC),
    )

    workflow.run_enrichment_request(
        EnrichmentRequest(
            source_system="twilio",
            case_type="WISMO",
            lookup=LookupCriteria(customer_phone="+1 (555) 555-5555"),
        )
    )

    assert oms_client.last_request is not None
    assert oms_client.last_request["customer_phone"] == "5555555555"


def test_latest_order_by_contact_returns_one_order_snapshot() -> None:
    oms_client = MockOmsClient(FIXTURE)
    workflow = EnrichTicketWithOrdersWorkflow(
        oms_client=oms_client,
        now_provider=lambda: datetime(2026, 6, 4, tzinfo=UTC),
    )

    response = workflow.run_latest_order_by_contact(
        EnrichmentRequest(
            source_system="twilio",
            case_type="WISMO",
            lookup=LookupCriteria(customer_phone="+15555555555"),
        )
    )

    assert response.metadata["operation"] == "latest_order_by_contact"
    assert response.matched_order_count == 1
    assert len(response.matched_orders) == 1
    assert response.metadata["returned_order_count"] == 1


def test_recent_orders_by_contact_requires_contact_lookup() -> None:
    oms_client = MockOmsClient(FIXTURE)
    workflow = EnrichTicketWithOrdersWorkflow(
        oms_client=oms_client,
        now_provider=lambda: datetime(2026, 6, 4, tzinfo=UTC),
    )

    try:
        workflow.run_recent_orders_by_contact(
            EnrichmentRequest(
                source_system="twilio",
                case_type="WISMO",
                lookup=LookupCriteria(order_reference="wlm-000000000000000"),
            )
        )
    except ValueError as exc:
        message = str(exc)
    else:
        raise AssertionError("Expected ValueError")

    assert "customer_phone or customer_email" in message


def test_generic_enrichment_request_can_search_by_order_reference() -> None:
    oms_client = MockOmsClient(FIXTURE)
    workflow = EnrichTicketWithOrdersWorkflow(
        oms_client=oms_client,
        now_provider=lambda: datetime(2026, 6, 4, tzinfo=UTC),
    )

    response = workflow.run_enrichment_request(
        EnrichmentRequest(
            source_system="twilio",
            source_record_id="sms-001",
            case_type="WISMO",
            lookup=LookupCriteria(order_reference="wlm-000000000000000"),
        )
    )

    assert response.source_system == "twilio"
    assert response.source_record_id == "sms-001"
    assert response.case_type == "WISMO"
    assert response.normalized_case_type == "wismo"
    assert response.match_status == "single_match"
    assert response.matched_order_count == 1
    assert response.result.delivery_status == "Delivered"
    assert oms_client.last_request["order_number"] == "wlm-000000000000000"
    assert response.metadata["matched_by"] == "order_reference"
    assert response.matched_orders[0].marketplace == "walmart_main"
    assert response.matched_orders[0].customer.email == "customer@example.com"
    assert response.matched_orders[0].shipments[0].tracking_status == "Delivered"
    assert response.matched_orders[0].shipments[0].tracking_url == (
        "https://www.fedex.com/fedextrack/?trknbr=999999999999"
    )
    assert response.matched_orders[0].order_date == "May 12, 2026, 5:20 PM ET"
    assert response.matched_orders[0].shipments[0].eta == "May 14, 2026, 8:00 PM ET"
    assert response.matched_orders[0].shipments[0].first_scan_date == "May 15, 2026, 1:34 PM ET"
    assert response.metadata["matched_orders"][0]["shipments"][0]["tracking_url"] == (
        "https://www.fedex.com/fedextrack/?trknbr=999999999999"
    )


def test_order_management_base_url_is_normalized_when_hash_fragment_is_missing() -> None:
    oms_client = MockOmsClient(FIXTURE)
    workflow = EnrichTicketWithOrdersWorkflow(
        oms_client=oms_client,
        order_management_base_url="https://ds.utires.com/order_management/",
        now_provider=lambda: datetime(2026, 6, 4, tzinfo=UTC),
    )

    update = workflow.run(
        HelpdeskRequest(
            ticket_id="12345",
            customer=Customer(phone="+15555555555"),
            ticket=TicketContext(channel="freshdesk"),
        ),
        dry_run=True,
    )

    assert (
        update.custom_fields["order_link"]
        == "https://ds.utires.com/order_management/#order=wlm-000000000000000"
    )
    assert (
        update.metadata["matched_orders"][0]["order_link"]
        == "https://ds.utires.com/order_management/#order=wlm-000000000000000"
    )


def test_unknown_case_type_does_not_block_wismo_flow() -> None:
    oms_client = MockOmsClient(FIXTURE)
    workflow = EnrichTicketWithOrdersWorkflow(
        oms_client=oms_client,
        now_provider=lambda: datetime(2026, 6, 4, tzinfo=UTC),
    )

    response = workflow.run_enrichment_request(
        EnrichmentRequest(
            source_system="helpdesk",
            case_type="Something Else",
            lookup=LookupCriteria(customer_phone="+15555555555"),
        )
    )

    assert response.normalized_case_type == "unknown"
    assert response.matched_order_count == 1


def test_generic_enrichment_request_requires_lookup_input() -> None:
    oms_client = MockOmsClient(FIXTURE)
    workflow = EnrichTicketWithOrdersWorkflow(
        oms_client=oms_client,
        now_provider=lambda: datetime(2026, 6, 4, tzinfo=UTC),
    )

    try:
        workflow.run_enrichment_request(
            EnrichmentRequest(source_system="helpdesk", lookup=LookupCriteria())
        )
    except ValueError as exc:
        message = str(exc)
    else:
        raise AssertionError("Expected ValueError")

    assert "At least one lookup field is required" in message


def test_wismo_returns_no_match_for_old_order() -> None:
    oms_client = MockOmsClient(FIXTURE)
    workflow = EnrichTicketWithOrdersWorkflow(
        oms_client=oms_client,
        now_provider=lambda: datetime(2026, 7, 30, tzinfo=UTC),
    )

    response = workflow.run_enrichment_request(
        EnrichmentRequest(
            source_system="helpdesk",
            case_type="WISMO",
            lookup=LookupCriteria(customer_phone="+15555555555"),
        )
    )

    assert response.match_status == "no_match"
    assert response.matched_order_count == 0
    assert response.result.order_summary == "No matching WISMO orders found."


def test_freshdesk_recent_orders_update_uses_helpdesk_adapter_when_not_dry_run() -> None:
    oms_client = MockOmsClient(FIXTURE)
    helpdesk_adapter = MockHelpdeskAdapter()
    workflow = EnrichTicketWithOrdersWorkflow(
        oms_client=oms_client,
        helpdesk_adapter=helpdesk_adapter,
        now_provider=lambda: datetime(2026, 6, 4, tzinfo=UTC),
    )

    update = workflow.run_freshdesk_recent_orders_update(
        FreshdeskRecentOrdersRequest(
            ticket_id="fd-123",
            customer_phone="+1 (555) 123-4567",
            customer_email="customer@example.com",
        ),
        dry_run=False,
    )

    assert update.ticket_id == "fd-123"
    assert update.custom_fields["delivery_status"] == "Delivered"
    assert len(helpdesk_adapter.applied_updates) == 1
    assert helpdesk_adapter.applied_updates[0].ticket_id == "fd-123"


class PartialMatchOmsClient(MockOmsClient):
    def search_orders(self, **kwargs):  # type: ignore[override]
        response = super().search_orders(**kwargs)
        if kwargs.get("filter_mode") == "all":
            response["orders"] = []
            response["order_count"] = 0
        return response


def test_partial_contact_match_adds_agent_warning_and_note() -> None:
    oms_client = PartialMatchOmsClient(FIXTURE)
    workflow = EnrichTicketWithOrdersWorkflow(
        oms_client=oms_client,
        now_provider=lambda: datetime(2026, 6, 4, tzinfo=UTC),
    )

    response = workflow.run_recent_orders_by_contact_or_reference(
        EnrichmentRequest(
            source_system="freshdesk",
            case_type="WISMO",
            lookup=LookupCriteria(
                customer_phone="+1 (555) 123-4567",
                customer_email="different@example.com",
            ),
        )
    )

    assert response.metadata["matched_by"] == "contact_partial_phone"
    assert response.metadata["match_quality"] == "partial_contact_match"
    assert response.metadata["exact_contact_match_found"] is False
    assert response.metadata["lookup_attempts"][1]["stage"] == "contact_partial_phone"
    assert response.metadata["lookup_attempts"][1]["used"]["customer_phone"] == "5551234567"
    assert "filter_mode" not in response.metadata["lookup_attempts"][1]["used"]
    assert response.metadata["contact_match_details"]["matched_on"] == ["customer_phone"]
    assert response.metadata["contact_match_details"]["mismatched_on"] == ["customer_email"]
    assert (
        "No exact match was found for the provided contact data."
        in response.result.private_note
    )
    assert any(
        "Partial contact match only" in warning
        for warning in response.metadata["warnings"]
    )

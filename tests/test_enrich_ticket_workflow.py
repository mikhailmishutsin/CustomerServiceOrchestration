from pathlib import Path

from cs_orchestration.domain.models import Customer, HelpdeskRequest, TicketContext
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
    workflow = EnrichTicketWithOrdersWorkflow(oms_client=oms_client)

    update = workflow.run(request, dry_run=True)

    assert update.ticket_id == "12345"
    assert update.metadata["dry_run"] is True
    assert update.metadata["uses_expand"] is True
    assert update.metadata["order_count"] == 1
    assert "Latest order wlm-000000000000000" in update.custom_fields["order_summary"]
    assert "Delivered" in update.private_note
    assert oms_client.last_request["expand"] is True


def test_filter_mode_is_optional() -> None:
    request = HelpdeskRequest(
        ticket_id="12345",
        customer=Customer(phone="+15555555555"),
        ticket=TicketContext(channel="freshdesk"),
    )
    oms_client = MockOmsClient(FIXTURE)
    workflow = EnrichTicketWithOrdersWorkflow(oms_client=oms_client)

    workflow.run(request)

    assert oms_client.last_request["filter_mode"] is None

from cs_orchestration.domain.models import (
    EnrichmentRequest,
    FreshdeskRecentOrdersRequest,
    TicketContext,
)


def to_recent_orders_enrichment_request(
    request: FreshdeskRecentOrdersRequest,
    *,
    return_limit: int = 3,
) -> EnrichmentRequest:
    """Translate Freshdesk's request and display limit into the core contract."""
    return EnrichmentRequest(
        source_system="freshdesk",
        source_record_id=request.ticket_id,
        case_type="WISMO",
        # OMS applies this limit at the source; the core API stays channel-neutral.
        max_records=return_limit,
        lookup={
            "customer_phone": request.customer_phone,
            "customer_email": request.customer_email,
            "order_reference": request.order_number,
        },
        ticket=TicketContext(channel="freshdesk", source="freshdesk"),
    )

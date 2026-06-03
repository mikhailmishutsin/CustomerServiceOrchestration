from typing import Literal

from cs_orchestration.domain.models import HelpdeskRequest, HelpdeskUpdate
from cs_orchestration.domain.summaries import build_support_summary
from cs_orchestration.integrations.helpdesk.base import HelpdeskAdapter
from cs_orchestration.integrations.oms.mapper import normalize_search_orders_response
from cs_orchestration.integrations.oms.mock_client import MockOmsClient


FilterMode = Literal["all", "any"]


class EnrichTicketWithOrdersWorkflow:
    def __init__(
        self,
        *,
        oms_client: MockOmsClient,
        helpdesk_adapter: HelpdeskAdapter | None = None,
    ) -> None:
        self.oms_client = oms_client
        self.helpdesk_adapter = helpdesk_adapter

    def run(
        self,
        request: HelpdeskRequest,
        *,
        dry_run: bool = True,
        limit: int = 5,
        filter_mode: FilterMode | None = None,
    ) -> HelpdeskUpdate:
        raw_response = self.oms_client.search_orders(
            customer_phone=request.customer.phone,
            customer_email=request.customer.email,
            customer_full_name=request.customer.name,
            filter_mode=filter_mode,
            expand=True,
            limit=limit,
        )
        orders = normalize_search_orders_response(raw_response)
        summary = build_support_summary(request, orders)

        update = HelpdeskUpdate(
            ticket_id=request.ticket_id,
            private_note=summary.private_note,
            custom_fields={
                "order_summary": summary.short_summary,
                "order_link": summary.latest_order_link,
            },
            tags=["oms-enriched"] if orders else ["oms-no-match"],
            metadata={
                "source": "orchestration-layer",
                "dry_run": dry_run,
                "confidence": summary.confidence,
                "warnings": summary.warnings,
                "order_count": len(orders),
                "uses_expand": True,
            },
        )

        if dry_run or self.helpdesk_adapter is None:
            return update
        return self.helpdesk_adapter.apply_update(update)

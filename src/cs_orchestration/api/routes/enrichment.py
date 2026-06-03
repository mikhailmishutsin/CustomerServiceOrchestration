from fastapi import APIRouter

from cs_orchestration.config.settings import settings
from cs_orchestration.domain.models import HelpdeskRequest, HelpdeskUpdate
from cs_orchestration.integrations.oms.mock_client import MockOmsClient
from cs_orchestration.workflows.enrich_ticket import EnrichTicketWithOrdersWorkflow

router = APIRouter()


@router.post("/enrich-ticket", response_model=HelpdeskUpdate)
def enrich_ticket(request: HelpdeskRequest) -> HelpdeskUpdate:
    workflow = EnrichTicketWithOrdersWorkflow(
        oms_client=MockOmsClient(settings.mock_oms_path)
    )
    return workflow.run(request, dry_run=settings.dry_run)

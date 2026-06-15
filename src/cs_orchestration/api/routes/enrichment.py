import logging
from secrets import compare_digest
from time import perf_counter

from fastapi import APIRouter, Depends, Header, HTTPException, status

from cs_orchestration.config.settings import settings
from cs_orchestration.domain.models import (
    EnrichmentRequest,
    EnrichmentResponse,
    FreshdeskRecentOrdersRequest,
    HelpdeskRequest,
    HelpdeskUpdate,
)
from cs_orchestration.integrations.helpdesk.freshdesk_adapter import (
    FreshdeskAdapter,
    FreshdeskApiError,
)
from cs_orchestration.integrations.oms.factory import build_order_business_client
from cs_orchestration.integrations.oms.real_client import OrderBusinessApiError
from cs_orchestration.workflows.enrich_ticket import EnrichTicketWithOrdersWorkflow


logger = logging.getLogger(__name__)


def _require_inbound_api_key(
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> None:
    if settings.inbound_api_key is None:
        return
    if x_api_key is None or not compare_digest(x_api_key, settings.inbound_api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid inbound API key.",
        )


router = APIRouter(dependencies=[Depends(_require_inbound_api_key)])


def _error_detail(message: str, debug: dict | None = None) -> str | dict:
    if not settings.expose_debug_errors or debug is None:
        return message
    return {
        "message": message,
        "debug": debug,
    }


@router.post("/enrich-ticket", response_model=HelpdeskUpdate)
def enrich_ticket(request: HelpdeskRequest) -> HelpdeskUpdate:
    workflow = _workflow()
    oms_client = workflow.oms_client
    try:
        return workflow.run(request, dry_run=settings.dry_run)
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=_error_detail(
                str(exc),
                {
                    "order_business_request": getattr(
                        oms_client, "last_request_debug", None
                    )
                },
            ),
        ) from None
    except OrderBusinessApiError as exc:
        raise HTTPException(
            status_code=502,
            detail=_error_detail(
                str(exc),
                {
                    "order_business_request": getattr(
                        oms_client, "last_request_debug", None
                    )
                },
            ),
        ) from None


@router.post("/enrichment/resolve", response_model=EnrichmentResponse)
def resolve_enrichment(request: EnrichmentRequest) -> EnrichmentResponse:
    workflow = _workflow()
    oms_client = workflow.oms_client
    try:
        return workflow.run_enrichment_request(request, dry_run=settings.dry_run)
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=_error_detail(
                str(exc),
                {
                    "order_business_request": getattr(
                        oms_client, "last_request_debug", None
                    )
                },
            ),
        ) from None
    except OrderBusinessApiError as exc:
        raise HTTPException(
            status_code=502,
            detail=_error_detail(
                str(exc),
                {
                    "order_business_request": getattr(
                        oms_client, "last_request_debug", None
                    )
                },
            ),
        ) from None


@router.post("/orders/latest-by-contact", response_model=EnrichmentResponse)
def latest_order_by_contact(request: EnrichmentRequest) -> EnrichmentResponse:
    workflow = _workflow()
    oms_client = workflow.oms_client
    try:
        return workflow.run_latest_order_by_contact(request, dry_run=settings.dry_run)
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=_error_detail(
                str(exc),
                {
                    "order_business_request": getattr(
                        oms_client, "last_request_debug", None
                    )
                },
            ),
        ) from None
    except OrderBusinessApiError as exc:
        raise HTTPException(
            status_code=502,
            detail=_error_detail(
                str(exc),
                {
                    "order_business_request": getattr(
                        oms_client, "last_request_debug", None
                    )
                },
            ),
        ) from None


@router.post("/orders/recent-by-contact", response_model=EnrichmentResponse)
def recent_orders_by_contact(request: EnrichmentRequest) -> EnrichmentResponse:
    workflow = _workflow()
    oms_client = workflow.oms_client
    try:
        return workflow.run_recent_orders_by_contact(request, dry_run=settings.dry_run)
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=_error_detail(
                str(exc),
                {
                    "order_business_request": getattr(
                        oms_client, "last_request_debug", None
                    )
                },
            ),
        ) from None


@router.post("/freshdesk/recent-orders", response_model=HelpdeskUpdate)
def freshdesk_recent_orders(request: FreshdeskRecentOrdersRequest) -> HelpdeskUpdate:
    started = perf_counter()
    logger.info(
        "freshdesk_recent_orders.request_received ticket_id=%s dry_run=%s has_phone=%s has_email=%s has_order_number=%s",
        request.ticket_id,
        settings.dry_run,
        bool(request.customer_phone),
        bool(request.customer_email),
        bool(request.order_number),
    )
    workflow = _workflow()
    oms_client = workflow.oms_client
    try:
        update = workflow.run_freshdesk_recent_orders_update(
            request,
            dry_run=settings.dry_run,
        )
        logger.info(
            "freshdesk_recent_orders.request_finished ticket_id=%s status=success duration_ms=%s matched_order_count=%s",
            request.ticket_id,
            round((perf_counter() - started) * 1000, 2),
            update.metadata.get("order_count"),
        )
        return update
    except ValueError as exc:
        logger.warning(
            "freshdesk_recent_orders.request_failed ticket_id=%s status=bad_request duration_ms=%s error=%s",
            request.ticket_id,
            round((perf_counter() - started) * 1000, 2),
            str(exc),
        )
        raise HTTPException(
            status_code=400,
            detail=_error_detail(
                str(exc),
                {
                    "order_business_request": getattr(oms_client, "last_request_debug", None)
                },
            ),
        ) from None
    except OrderBusinessApiError as exc:
        logger.exception(
            "freshdesk_recent_orders.request_failed ticket_id=%s status=oms_error duration_ms=%s",
            request.ticket_id,
            round((perf_counter() - started) * 1000, 2),
        )
        raise HTTPException(
            status_code=502,
            detail=_error_detail(
                str(exc),
                {
                    "order_business_request": getattr(
                        oms_client, "last_request_debug", None
                    )
                },
            ),
        ) from None
    except FreshdeskApiError as exc:
        logger.exception(
            "freshdesk_recent_orders.request_failed ticket_id=%s status=freshdesk_error duration_ms=%s",
            request.ticket_id,
            round((perf_counter() - started) * 1000, 2),
        )
        raise HTTPException(
            status_code=502,
            detail=_error_detail(
                str(exc),
                {
                    "order_business_request": getattr(oms_client, "last_request_debug", None),
                    "freshdesk_request": getattr(
                        workflow.helpdesk_adapter,
                        "last_request_debug",
                        None,
                    ),
                },
            ),
        ) from None


def _workflow() -> EnrichTicketWithOrdersWorkflow:
    oms_client = build_order_business_client(settings)
    helpdesk_adapter = None
    if settings.freshdesk.base_url and settings.freshdesk.api_key:
        helpdesk_adapter = FreshdeskAdapter(
            base_url=settings.freshdesk.base_url,
            api_key=settings.freshdesk.api_key,
        )
    return EnrichTicketWithOrdersWorkflow(
        oms_client=oms_client,
        helpdesk_adapter=helpdesk_adapter,
        order_management_base_url=settings.order_management_base_url,
    )

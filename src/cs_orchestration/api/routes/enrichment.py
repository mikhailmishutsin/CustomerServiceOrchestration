import logging
from collections.abc import Callable
from secrets import compare_digest
from time import perf_counter
from typing import TypeVar

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
from cs_orchestration.integrations.helpdesk.freshdesk_mapper import (
    to_recent_orders_enrichment_request,
)
from cs_orchestration.integrations.oms.factory import build_order_business_client
from cs_orchestration.integrations.oms.real_client import OrderBusinessApiError
from cs_orchestration.workflows.enrich_ticket import EnrichTicketWithOrdersWorkflow


logger = logging.getLogger(__name__)
T = TypeVar("T")


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


def _run_core_operation(
    operation: Callable[[EnrichTicketWithOrdersWorkflow], T],
) -> T:
    """Run a channel-neutral operation with the standard OMS error response."""
    workflow = _workflow()
    oms_client = workflow.oms_client
    try:
        return operation(workflow)
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


@router.post("/enrich-ticket", response_model=HelpdeskUpdate)
def enrich_ticket(request: HelpdeskRequest) -> HelpdeskUpdate:
    return _run_core_operation(
        lambda workflow: workflow.run(request, dry_run=settings.dry_run)
    )


@router.post("/enrichment/resolve", response_model=EnrichmentResponse)
def resolve_enrichment(request: EnrichmentRequest) -> EnrichmentResponse:
    return _run_core_operation(
        lambda workflow: workflow.run_enrichment_request(
            request,
            dry_run=settings.dry_run,
        )
    )


@router.post("/orders/latest-by-contact", response_model=EnrichmentResponse)
def latest_order_by_contact(request: EnrichmentRequest) -> EnrichmentResponse:
    return _run_core_operation(
        lambda workflow: workflow.run_latest_order_by_contact(
            request,
            dry_run=settings.dry_run,
        )
    )


@router.post("/orders/recent-by-contact", response_model=EnrichmentResponse)
def recent_orders_by_contact(request: EnrichmentRequest) -> EnrichmentResponse:
    return _run_core_operation(
        lambda workflow: workflow.run_recent_orders_by_contact(
            request,
            dry_run=settings.dry_run,
        )
    )


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
    freshdesk_adapter: FreshdeskAdapter | None = None
    try:
        enrichment_started = perf_counter()
        result = workflow.run_recent_orders_by_contact_or_reference(
            to_recent_orders_enrichment_request(request),
            dry_run=settings.dry_run,
        )
        enrichment_duration_ms = round((perf_counter() - enrichment_started) * 1000, 2)
        update = workflow.build_helpdesk_update(ticket_id=request.ticket_id, result=result)
        update = workflow.add_timing_metadata(
            update,
            {
                "oms_enrichment_ms": enrichment_duration_ms,
                "freshdesk_write_ms": None,
                "total_ms": round((perf_counter() - started) * 1000, 2),
            },
        )
        freshdesk_adapter = _freshdesk_adapter()
        if not settings.dry_run and freshdesk_adapter is not None:
            write_started = perf_counter()
            update = freshdesk_adapter.apply_update(update)
            update = workflow.add_timing_metadata(
                update,
                {
                    "oms_enrichment_ms": enrichment_duration_ms,
                    "freshdesk_write_ms": round((perf_counter() - write_started) * 1000, 2),
                    "total_ms": round((perf_counter() - started) * 1000, 2),
                },
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
                        freshdesk_adapter,
                        "last_request_debug",
                        None,
                    ),
                },
            ),
        ) from None


def _workflow() -> EnrichTicketWithOrdersWorkflow:
    oms_client = build_order_business_client(settings)
    return EnrichTicketWithOrdersWorkflow(
        oms_client=oms_client,
        order_management_base_url=settings.order_management_base_url,
    )


def _freshdesk_adapter() -> FreshdeskAdapter | None:
    if settings.freshdesk.base_url and settings.freshdesk.api_key:
        return FreshdeskAdapter(
            base_url=settings.freshdesk.base_url,
            api_key=settings.freshdesk.api_key,
        )
    return None

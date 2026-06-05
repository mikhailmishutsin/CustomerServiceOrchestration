from datetime import UTC, datetime, timedelta
from typing import Callable, Literal

from cs_orchestration.domain.models import (
    Customer,
    EnrichmentRequest,
    EnrichmentResponse,
    EnrichmentResult,
    FreshdeskRecentOrdersRequest,
    HelpdeskRequest,
    HelpdeskUpdate,
    OrderSnapshot,
    Order,
    ShipmentSnapshot,
    TicketContext,
)
from cs_orchestration.domain.summaries import build_support_summary
from cs_orchestration.integrations.helpdesk.base import HelpdeskAdapter
from cs_orchestration.integrations.oms.base import OrderBusinessClient
from cs_orchestration.integrations.oms.mapper import normalize_search_orders_response


FilterMode = Literal["all", "any"]
NormalizedCaseType = Literal["wismo", "unknown"]
LookupStage = Literal[
    "contact_exact",
    "contact_partial_phone",
    "contact_partial_email",
    "contact_single_field",
    "order_reference",
    "customer_name",
]


class EnrichTicketWithOrdersWorkflow:
    def __init__(
        self,
        *,
        oms_client: OrderBusinessClient,
        helpdesk_adapter: HelpdeskAdapter | None = None,
        order_management_base_url: str = "https://ds.utires.com/order_management/#order=",
        now_provider: Callable[[], datetime] | None = None,
    ) -> None:
        self.oms_client = oms_client
        self.helpdesk_adapter = helpdesk_adapter
        self.order_management_base_url = order_management_base_url
        self.now_provider = now_provider or (lambda: datetime.now(UTC))

    def run(
        self,
        request: HelpdeskRequest,
        *,
        dry_run: bool = True,
        limit: int = 5,
        filter_mode: FilterMode | None = None,
    ) -> HelpdeskUpdate:
        generic_request = self._from_helpdesk_request(request)
        result = self.run_enrichment_request(
            generic_request,
            dry_run=dry_run,
            limit=limit,
            filter_mode=filter_mode,
        )
        update = self._build_helpdesk_update(ticket_id=request.ticket_id, result=result)

        if dry_run or self.helpdesk_adapter is None:
            return update
        return self.helpdesk_adapter.apply_update(update)

    def run_freshdesk_recent_orders(
        self,
        request: FreshdeskRecentOrdersRequest,
        *,
        dry_run: bool = True,
        max_records: int = 3,
        filter_mode: FilterMode | None = None,
    ) -> EnrichmentResponse:
        return self.run_recent_orders_by_contact_or_reference(
            EnrichmentRequest(
                source_system="freshdesk",
                source_record_id=request.ticket_id,
                case_type="WISMO",
                max_records=max_records,
                lookup={
                    "customer_phone": request.customer_phone,
                    "customer_email": request.customer_email,
                    "order_reference": request.order_number,
                },
                ticket=TicketContext(channel="freshdesk", source="freshdesk"),
            ),
            dry_run=dry_run,
            filter_mode=filter_mode,
        )

    def run_freshdesk_recent_orders_update(
        self,
        request: FreshdeskRecentOrdersRequest,
        *,
        dry_run: bool = True,
        max_records: int = 3,
        filter_mode: FilterMode | None = None,
    ) -> HelpdeskUpdate:
        result = self.run_freshdesk_recent_orders(
            request,
            dry_run=dry_run,
            max_records=max_records,
            filter_mode=filter_mode,
        )
        update = self._build_helpdesk_update(
            ticket_id=request.ticket_id,
            result=result,
        )
        if dry_run or self.helpdesk_adapter is None:
            return update
        return self.helpdesk_adapter.apply_update(update)

    def run_enrichment_request(
        self,
        request: EnrichmentRequest,
        *,
        dry_run: bool = True,
        limit: int = 5,
        filter_mode: FilterMode | None = None,
    ) -> EnrichmentResponse:
        return self._run_order_lookup(
            request,
            dry_run=dry_run,
            search_limit=limit,
            return_limit=None,
            filter_mode=filter_mode,
            operation="wismo_resolve",
        )

    def run_latest_order_by_contact(
        self,
        request: EnrichmentRequest,
        *,
        dry_run: bool = True,
        search_limit: int = 10,
        filter_mode: FilterMode | None = None,
    ) -> EnrichmentResponse:
        self._validate_contact_lookup(request)
        return self._run_order_lookup(
            request,
            dry_run=dry_run,
            search_limit=request.max_records or search_limit,
            return_limit=1,
            filter_mode=filter_mode,
            operation="latest_order_by_contact",
        )

    def run_recent_orders_by_contact(
        self,
        request: EnrichmentRequest,
        *,
        dry_run: bool = True,
        search_limit: int = 10,
        return_limit: int = 10,
        filter_mode: FilterMode | None = None,
    ) -> EnrichmentResponse:
        self._validate_contact_lookup(request)
        return self._run_order_lookup(
            request,
            dry_run=dry_run,
            search_limit=request.max_records or search_limit,
            return_limit=None,
            filter_mode=filter_mode,
            operation="recent_orders_by_contact",
        )

    def run_recent_orders_by_contact_or_reference(
        self,
        request: EnrichmentRequest,
        *,
        dry_run: bool = True,
        search_limit: int = 10,
        filter_mode: FilterMode | None = None,
    ) -> EnrichmentResponse:
        self._validate_recent_lookup(request)
        return self._run_order_lookup(
            request,
            dry_run=dry_run,
            search_limit=request.max_records or search_limit,
            return_limit=None,
            filter_mode=filter_mode,
            operation="recent_orders_by_contact_or_reference",
        )

    def _run_order_lookup(
        self,
        request: EnrichmentRequest,
        *,
        dry_run: bool,
        search_limit: int,
        return_limit: int | None,
        filter_mode: FilterMode | None,
        operation: str,
    ) -> EnrichmentResponse:
        self._validate_lookup(request)
        raw_response, matched_by, lookup_attempts = self._search_with_priority(
            request,
            limit=search_limit,
            filter_mode=filter_mode,
        )
        raw_orders = normalize_search_orders_response(raw_response)
        self._attach_agent_links(raw_orders)
        orders = self._filter_wismo_orders(raw_orders)
        contact_match_summary = self._contact_match_summary(request, orders, matched_by)
        total_matching_orders = len(orders)
        if return_limit is not None:
            orders = orders[:return_limit]
        summary = build_support_summary(
            self._to_helpdesk_summary_request(request),
            orders,
        )
        private_note = summary.private_note
        warnings = list(summary.warnings)
        if contact_match_summary["message"]:
            private_note = f"{contact_match_summary['message']}\n\n{private_note}"
        if contact_match_summary["warning"]:
            warnings.append(contact_match_summary["warning"])
        match_status = self._match_status(total_matching_orders)
        if match_status == "multiple_match":
            warnings.append(
                "Multiple recent orders found. Ask for the last 4 digits of the order number to confirm the correct order."
            )

        return EnrichmentResponse(
            source_system=request.source_system,
            source_record_id=request.source_record_id,
            request_type=request.request_type,
            case_type=request.case_type,
            normalized_case_type=self._normalize_case_type(request),
            match_status=match_status,
            matched_order_count=total_matching_orders,
            matched_orders=[self._build_order_snapshot(order) for order in orders],
            result=EnrichmentResult(
                order_summary=summary.short_summary,
                private_note=private_note,
                order_link=summary.latest_order_link,
                delivery_status=summary.latest_delivery_status,
                delivery_eta=summary.latest_delivery_eta,
                order_date=summary.latest_order_date,
            ),
            metadata={
                "source": "orchestration-layer",
                "source_system": request.source_system,
                "request_type": request.request_type,
                "case_type": request.case_type,
                "normalized_case_type": self._normalize_case_type(request),
                "operation": operation,
                "dry_run": dry_run,
                "confidence": summary.confidence,
                "warnings": warnings,
                "search_window_note": "WISMO checks orders placed within the last 30 days.",
                "search_window_days": 30,
                "oms_max_records": search_limit,
                "order_count": total_matching_orders,
                "returned_order_count": len(orders),
                "raw_order_count": len(raw_orders),
                "uses_expand": True,
                "matched_by": matched_by,
                "match_quality": contact_match_summary["match_quality"],
                "exact_contact_match_found": contact_match_summary["exact_contact_match_found"],
                "contact_match_details": contact_match_summary["details"],
                "lookup_used": {
                    "order_reference": request.lookup.order_reference,
                    "customer_email": request.lookup.customer_email,
                    "customer_phone": request.lookup.customer_phone,
                    "customer_phone_normalized": self._normalize_phone_for_oms(
                        request.lookup.customer_phone
                    ),
                    "customer_name": request.lookup.customer_name,
                    "filter_mode": filter_mode,
                },
                "lookup_attempts": lookup_attempts,
                "debug": {
                    "order_business_request": getattr(
                        self.oms_client, "last_request_debug", None
                    )
                },
            },
        )

    def _attach_agent_links(self, orders: list[Order]) -> None:
        for order in orders:
            if order.details_ref is None:
                continue
            order_ref = order.details_ref.order_number or order.order_number
            if not order_ref:
                continue
            order.details_ref.safe_agent_url = (
                f"{self.order_management_base_url}{order_ref}"
            )

    def _search_with_priority(
        self,
        request: EnrichmentRequest,
        *,
        limit: int,
        filter_mode: FilterMode | None,
    ) -> tuple[dict, LookupStage | None, list[dict[str, object]]]:
        lookup_attempts: list[dict[str, object]] = []
        normalized_phone = self._normalize_phone_for_oms(request.lookup.customer_phone)
        normalized_email = self._normalize_email(request.lookup.customer_email)

        attempts: list[tuple[LookupStage, dict[str, object]]] = []
        if normalized_phone and normalized_email:
            attempts.append(
                (
                    "contact_exact",
                    {
                        "customer_phone": normalized_phone,
                        "customer_email": normalized_email,
                        "filter_mode": "all",
                    },
                )
            )
            attempts.extend(
                [
                    (
                        "contact_partial_phone",
                        {
                            "customer_phone": normalized_phone,
                            "customer_email": None,
                            "filter_mode": None,
                        },
                    ),
                    (
                        "contact_partial_email",
                        {
                            "customer_phone": None,
                            "customer_email": normalized_email,
                            "filter_mode": None,
                        },
                    ),
                ]
            )
        elif normalized_phone or normalized_email:
            attempts.append(
                (
                    "contact_single_field",
                    {
                        "customer_phone": normalized_phone,
                        "customer_email": normalized_email,
                        "filter_mode": filter_mode,
                    },
                )
            )
        if request.lookup.order_reference:
            attempts.append(
                (
                    "order_reference",
                    {
                        "order_number": request.lookup.order_reference,
                        "filter_mode": None,
                    },
                )
            )
        if request.lookup.customer_name:
            attempts.append(
                (
                    "customer_name",
                    {
                        "customer_full_name": request.lookup.customer_name,
                        "filter_mode": filter_mode,
                    },
                )
            )

        last_response: dict[str, object] = {"success": True, "orders": [], "order_count": 0}
        matched_by: LookupStage | None = None
        for stage, params in attempts:
            response = self.oms_client.search_orders(
                expand=True,
                limit=limit,
                **params,
            )
            order_count = len(response.get("orders", []))
            lookup_attempts.append(
                {
                    "stage": stage,
                    "used": {key: value for key, value in params.items() if value not in (None, "")},
                    "order_count": order_count,
                }
            )
            last_response = response
            if order_count > 0:
                matched_by = stage
                break

        return last_response, matched_by, lookup_attempts

    def _filter_wismo_orders(self, orders: list[Order]) -> list[Order]:
        cutoff = self.now_provider() - timedelta(days=30)
        filtered: list[Order] = []
        for order in orders:
            order_dt = self._parse_datetime(order.order_date)
            if order_dt is None:
                continue
            if order_dt < cutoff:
                continue
            filtered.append(order)
        return filtered

    @staticmethod
    def _match_status(order_count: int) -> str:
        if order_count == 0:
            return "no_match"
        if order_count == 1:
            return "single_match"
        return "multiple_match"

    def _build_order_snapshot(self, order: Order) -> OrderSnapshot:
        return OrderSnapshot(
            order_reference=order.order_number,
            order_date=self._format_datetime(order.order_date),
            marketplace=order.marketplace,
            customer=order.customer,
            order_link=order.details_ref.safe_agent_url if order.details_ref else None,
            shipments=[
                ShipmentSnapshot(
                    carrier=shipment.carrier,
                    tracking_number=shipment.tracking_number,
                    tracking_status=shipment.tracking_status,
                    tracking_details=shipment.tracking_description,
                    eta=self._format_datetime_range(
                        shipment.eta_start,
                        shipment.eta_end,
                    ),
                    first_scan_date=self._format_datetime(shipment.first_scan_date),
                    delivered_at=self._format_datetime(shipment.delivered_at),
                )
                for shipment in order.shipments
            ],
        )

    @staticmethod
    def _validate_lookup(request: EnrichmentRequest) -> None:
        if any(
            [
                request.lookup.order_reference,
                request.lookup.customer_email,
                request.lookup.customer_phone,
                request.lookup.customer_name,
            ]
        ):
            return
        raise ValueError(
            "At least one lookup field is required: order_reference, customer_phone, customer_email, or customer_name."
        )

    @staticmethod
    def _validate_contact_lookup(request: EnrichmentRequest) -> None:
        if request.lookup.customer_phone or request.lookup.customer_email:
            return
        raise ValueError(
            "At least one contact lookup field is required: customer_phone or customer_email."
        )

    @staticmethod
    def _validate_recent_lookup(request: EnrichmentRequest) -> None:
        if (
            request.lookup.customer_phone
            or request.lookup.customer_email
            or request.lookup.order_reference
        ):
            return
        raise ValueError(
            "At least one lookup field is required for recent orders: customer_phone, customer_email, or order_reference."
        )

    @staticmethod
    def _from_helpdesk_request(request: HelpdeskRequest) -> EnrichmentRequest:
        return EnrichmentRequest(
            source_system=request.ticket.channel or "helpdesk",
            source_record_id=request.ticket_id,
            case_type="WISMO",
            lookup={
                "customer_email": request.customer.email,
                "customer_phone": request.customer.phone,
                "customer_name": request.customer.name,
            },
            ticket=request.ticket,
        )

    @staticmethod
    def _build_helpdesk_update(
        *,
        ticket_id: str,
        result: EnrichmentResponse,
    ) -> HelpdeskUpdate:
        return HelpdeskUpdate(
            ticket_id=ticket_id,
            private_note=result.result.private_note,
            custom_fields={
                "order_summary": result.result.order_summary,
                "order_link": result.result.order_link,
                "delivery_status": result.result.delivery_status,
                "delivery_eta": result.result.delivery_eta,
                "order_date": result.result.order_date,
            },
            tags=["oms-enriched"] if result.matched_order_count else ["oms-no-match"],
            metadata=result.metadata,
        )

    @staticmethod
    def _to_helpdesk_summary_request(request: EnrichmentRequest) -> HelpdeskRequest:
        return HelpdeskRequest(
            ticket_id=request.source_record_id or "external-request",
            customer=Customer(
                name=request.lookup.customer_name,
                email=request.lookup.customer_email,
                phone=request.lookup.customer_phone,
            ),
            ticket=TicketContext(
                subject=request.request_type,
                description=request.ticket.description,
                source=request.ticket.source or request.source_system,
                channel=request.ticket.channel or request.source_system,
            ),
        )

    @staticmethod
    def _normalize_case_type(request: EnrichmentRequest) -> NormalizedCaseType:
        raw_value = (request.case_type or "").strip().lower()
        if raw_value in {"wismo", "where is my order", "where's my order"}:
            return "wismo"
        return "unknown"

    @staticmethod
    def _normalize_phone_for_oms(phone: str | None) -> str | None:
        if phone is None:
            return None
        digits = "".join(char for char in phone if char.isdigit())
        if not digits:
            return None
        if len(digits) == 11 and digits.startswith("1"):
            return digits[1:]
        return digits

    @staticmethod
    def _normalize_email(email: str | None) -> str | None:
        if email is None:
            return None
        normalized = email.strip().lower()
        return normalized or None

    def _contact_match_summary(
        self,
        request: EnrichmentRequest,
        orders: list[Order],
        matched_by: LookupStage | None,
    ) -> dict[str, object]:
        phone = self._normalize_phone_for_oms(request.lookup.customer_phone)
        email = self._normalize_email(request.lookup.customer_email)
        details = {
            "matched_on": [],
            "mismatched_on": [],
        }
        if not orders or matched_by not in {
            "contact_exact",
            "contact_partial_phone",
            "contact_partial_email",
            "contact_single_field",
        }:
            return {
                "match_quality": None,
                "exact_contact_match_found": None,
                "message": None,
                "warning": None,
                "details": details,
            }

        latest_order = orders[0]
        latest_phone = self._normalize_phone_for_oms(latest_order.customer.phone)
        latest_email = self._normalize_email(latest_order.customer.email)
        phone_matches = phone is not None and phone == latest_phone
        email_matches = email is not None and email == latest_email

        if phone is not None:
            (details["matched_on"] if phone_matches else details["mismatched_on"]).append(
                "customer_phone"
            )
        if email is not None:
            (details["matched_on"] if email_matches else details["mismatched_on"]).append(
                "customer_email"
            )

        if matched_by == "contact_exact":
            return {
                "match_quality": "exact_contact_match",
                "exact_contact_match_found": True,
                "message": None,
                "warning": None,
                "details": details,
            }

        if matched_by in {"contact_partial_phone", "contact_partial_email"}:
            matched_labels = self._humanize_contact_fields(details["matched_on"])
            mismatched_labels = self._humanize_contact_fields(details["mismatched_on"])
            return {
                "match_quality": "partial_contact_match",
                "exact_contact_match_found": False,
                "message": (
                    "No exact match was found for the provided contact data.\n"
                    f"Partial match found: matched on {matched_labels}, did not match on {mismatched_labels}."
                ),
                "warning": (
                    f"Partial contact match only: matched on {matched_labels}, did not match on {mismatched_labels}."
                ),
                "details": details,
            }

        return {
            "match_quality": "single_field_contact_match",
            "exact_contact_match_found": True,
            "message": None,
            "warning": None,
            "details": details,
        }

    @staticmethod
    def _humanize_contact_fields(fields: list[str]) -> str:
        mapping = {
            "customer_phone": "phone",
            "customer_email": "email",
        }
        labels = [mapping.get(field, field) for field in fields]
        if not labels:
            return "none"
        if len(labels) == 1:
            return labels[0]
        return " and ".join(labels)

    @staticmethod
    def _parse_datetime(value: str | None) -> datetime | None:
        if not value:
            return None
        normalized = value.strip()
        if not normalized:
            return None
        if normalized.endswith("Z"):
            normalized = normalized[:-1] + "+00:00"
        try:
            dt = datetime.fromisoformat(normalized)
        except ValueError:
            return None
        if dt.tzinfo is None:
            return dt.replace(tzinfo=UTC)
        return dt

    def _format_datetime(self, value: str | None) -> str | None:
        dt = self._parse_datetime(value)
        if dt is None:
            return None
        return f"{dt.strftime('%b %d, %Y')}, {self._format_time(dt)} {self._tz_label(dt)}"

    def _format_datetime_range(self, start: str | None, end: str | None) -> str | None:
        start_dt = self._parse_datetime(start)
        end_dt = self._parse_datetime(end)
        if start_dt and end_dt:
            if self._tz_label(start_dt) == self._tz_label(end_dt) and start_dt.date() == end_dt.date():
                return (
                    f"{start_dt.strftime('%b %d, %Y')}, "
                    f"{self._format_time(start_dt)} - {self._format_time(end_dt)} {self._tz_label(end_dt)}"
                )
            return f"{self._format_datetime(start)} to {self._format_datetime(end)}"
        if end_dt:
            return self._format_datetime(end)
        if start_dt:
            return self._format_datetime(start)
        return None

    @staticmethod
    def _format_time(dt: datetime) -> str:
        hour = dt.strftime("%I").lstrip("0") or "0"
        return f"{hour}:{dt.strftime('%M')} {dt.strftime('%p')}"

    @staticmethod
    def _tz_label(dt: datetime) -> str:
        offset = dt.utcoffset()
        if offset in (None, timedelta(0)):
            return "UTC"
        if offset in (timedelta(hours=-4), timedelta(hours=-5)):
            return "ET"
        total_minutes = int(offset.total_seconds() // 60)
        sign = "+" if total_minutes >= 0 else "-"
        absolute_minutes = abs(total_minutes)
        hours, minutes = divmod(absolute_minutes, 60)
        return f"UTC{sign}{hours:02d}:{minutes:02d}"

import logging
from time import perf_counter
from typing import Any

import httpx

from cs_orchestration.domain.models import HelpdeskUpdate
from cs_orchestration.integrations.helpdesk.freshdesk_note_renderer import (
    render_freshdesk_private_note,
)


class FreshdeskApiError(RuntimeError):
    """Raised when Freshdesk rejects a write-back request."""


logger = logging.getLogger(__name__)


class FreshdeskAdapter:
    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        client: httpx.Client | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self._client = client or httpx.Client(timeout=30.0)
        self.last_request_debug: dict[str, Any] | None = None

    def apply_update(self, update: HelpdeskUpdate) -> HelpdeskUpdate:
        started = perf_counter()
        request_url = f"{self.base_url}/api/v2/tickets/{update.ticket_id}/notes"
        payload = {
            "body": render_freshdesk_private_note(update),
            "private": True,
        }
        self.last_request_debug = {
            "service": "freshdesk",
            "operation": "create_private_note",
            "method": "POST",
            "url": request_url,
            "auth": {
                "type": "basic_api_key",
                "api_key": "[redacted]",
            },
            "json": payload,
        }

        logger.info(
            "freshdesk_adapter.create_note_started ticket_id=%s",
            update.ticket_id,
        )
        try:
            response = self._client.post(
                request_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                auth=(self.api_key, "X"),
            )
        except httpx.HTTPError as exc:
            logger.exception(
                "freshdesk_adapter.create_note_failed ticket_id=%s duration_ms=%s error_type=%s",
                update.ticket_id,
                round((perf_counter() - started) * 1000, 2),
                exc.__class__.__name__,
            )
            raise FreshdeskApiError(
                f"Freshdesk note request failed: {exc.__class__.__name__}."
            ) from None

        if response.status_code >= 400:
            logger.warning(
                "freshdesk_adapter.create_note_rejected ticket_id=%s duration_ms=%s status_code=%s",
                update.ticket_id,
                round((perf_counter() - started) * 1000, 2),
                response.status_code,
            )
            raise FreshdeskApiError(
                f"Freshdesk returned HTTP {response.status_code} while creating a private note."
            )

        note_data = response.json()
        metadata = dict(update.metadata)
        metadata["freshdesk"] = {
            "note_id": note_data.get("id"),
            "ticket_id": note_data.get("ticket_id"),
            "private": note_data.get("private"),
            "status_code": response.status_code,
        }
        logger.info(
            "freshdesk_adapter.create_note_finished ticket_id=%s duration_ms=%s note_id=%s status_code=%s",
            update.ticket_id,
            round((perf_counter() - started) * 1000, 2),
            note_data.get("id"),
            response.status_code,
        )
        return update.model_copy(update={"metadata": metadata})

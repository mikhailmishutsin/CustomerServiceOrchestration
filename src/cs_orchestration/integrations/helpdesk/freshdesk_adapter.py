from html import escape
from typing import Any

import httpx

from cs_orchestration.domain.models import HelpdeskUpdate


class FreshdeskApiError(RuntimeError):
    """Raised when Freshdesk rejects a write-back request."""


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
        request_url = f"{self.base_url}/api/v2/tickets/{update.ticket_id}/notes"
        payload = {
            "body": self._note_html(update.private_note),
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

        response = self._client.post(
            request_url,
            json=payload,
            headers={"Content-Type": "application/json"},
            auth=(self.api_key, "X"),
        )
        if response.status_code >= 400:
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
        return update.model_copy(update={"metadata": metadata})

    @staticmethod
    def _note_html(text: str) -> str:
        return "<div>" + escape(text).replace("\n", "<br />") + "</div>"

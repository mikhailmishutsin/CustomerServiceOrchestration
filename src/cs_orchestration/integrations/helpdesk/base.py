from typing import Protocol

from cs_orchestration.domain.models import HelpdeskUpdate


class HelpdeskAdapter(Protocol):
    def apply_update(self, update: HelpdeskUpdate) -> HelpdeskUpdate:
        """Apply a common helpdesk update through a concrete helpdesk provider."""

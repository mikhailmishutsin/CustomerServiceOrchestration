from cs_orchestration.domain.models import HelpdeskUpdate


class MockHelpdeskAdapter:
    def __init__(self) -> None:
        self.applied_updates: list[HelpdeskUpdate] = []

    def apply_update(self, update: HelpdeskUpdate) -> HelpdeskUpdate:
        self.applied_updates.append(update)
        return update

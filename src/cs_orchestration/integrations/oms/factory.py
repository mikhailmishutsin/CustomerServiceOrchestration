from cs_orchestration.config.settings import Settings
from cs_orchestration.integrations.oms.base import OrderBusinessClient
from cs_orchestration.integrations.oms.mock_client import MockOmsClient
from cs_orchestration.integrations.oms.real_client import OrderBusinessApiClient


def build_order_business_client(settings: Settings) -> OrderBusinessClient:
    if settings.integration_mode == "real":
        return OrderBusinessApiClient(settings.order_business_api)
    return MockOmsClient(settings.mock_oms_path)

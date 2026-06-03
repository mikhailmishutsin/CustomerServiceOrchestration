from pathlib import Path

from pydantic import BaseModel


class Settings(BaseModel):
    app_name: str = "Customer Service Orchestration"
    dry_run: bool = True
    mock_oms_path: Path = Path(
        "cs-orchestration-context/examples/oms-search-orders-response.json"
    )


settings = Settings()

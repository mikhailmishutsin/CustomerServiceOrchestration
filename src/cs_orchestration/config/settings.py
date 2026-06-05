from pathlib import Path
from os import getenv
from typing import Literal

from dotenv import load_dotenv
from pydantic import BaseModel


load_dotenv()


class ServiceCredentials(BaseModel):
    username: str | None = None
    password: str | None = None
    secret_key: str | None = None


AuthMode = Literal[
    "none",
    "query_secret",
    "query_user_secret",
    "basic",
    "basic_query_secret",
    "bearer",
]


class ServiceEndpoint(BaseModel):
    base_url: str | None = None
    credentials: ServiceCredentials = ServiceCredentials()
    auth_mode: AuthMode = "basic_query_secret"
    user_param: str = "user"
    secret_param: str = "secret_key"


class FreshdeskEndpoint(BaseModel):
    base_url: str | None = None
    api_key: str | None = None


AppEnv = Literal["local", "production"]


class Settings(BaseModel):
    app_name: str = "Customer Service Orchestration"
    app_env: AppEnv = "local"
    dry_run: bool = True
    integration_mode: Literal["mock", "real"] = "mock"
    inbound_api_key: str | None = None
    inbound_api_key_header: str = "X-API-Key"
    expose_docs: bool = True
    expose_debug_errors: bool = True
    order_management_base_url: str = "https://ds.utires.com/order_management/#order="
    mock_oms_path: Path = Path(
        "cs-orchestration-context/examples/oms-search-orders-response.json"
    )
    order_business_api: ServiceEndpoint = ServiceEndpoint(
        base_url=getenv("ORDER_BUSINESS_API_BASE_URL"),
        credentials=ServiceCredentials(
            username=getenv("ORDER_BUSINESS_API_USER"),
            password=getenv("ORDER_BUSINESS_API_PASSWORD"),
            secret_key=getenv("ORDER_BUSINESS_API_SECRET_KEY"),
        ),
    )
    fedex_api: ServiceEndpoint = ServiceEndpoint(
        base_url=getenv("FEDEX_API_BASE_URL"),
        credentials=ServiceCredentials(
            username=getenv("FEDEX_API_USER"),
            password=getenv("FEDEX_API_PASSWORD"),
            secret_key=getenv("FEDEX_API_SECRET_KEY"),
        ),
    )
    freshdesk: FreshdeskEndpoint = FreshdeskEndpoint(
        base_url=getenv("FRESHDESK_BASE_URL"),
        api_key=getenv("FRESHDESK_API_KEY"),
    )


def _env_bool(name: str, default: bool) -> bool:
    value = _env(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _env(name: str) -> str | None:
    value = getenv(name)
    if value is None or value == "":
        return None
    return value


def load_settings() -> Settings:
    app_env = getenv("APP_ENV", "local")
    default_expose_dev_routes = app_env != "production"
    return Settings(
        app_env=app_env,
        dry_run=_env_bool("DRY_RUN", True),
        integration_mode=getenv("INTEGRATION_MODE", "mock"),
        inbound_api_key=_env("INBOUND_API_KEY"),
        inbound_api_key_header=getenv("INBOUND_API_KEY_HEADER", "X-API-Key"),
        expose_docs=_env_bool("EXPOSE_DOCS", default_expose_dev_routes),
        expose_debug_errors=_env_bool("EXPOSE_DEBUG_ERRORS", default_expose_dev_routes),
        order_management_base_url=getenv(
            "ORDER_MANAGEMENT_BASE_URL",
            "https://ds.utires.com/order_management/#order=",
        ),
        order_business_api=ServiceEndpoint(
            base_url=getenv("ORDER_BUSINESS_API_BASE_URL"),
            credentials=ServiceCredentials(
                username=_env("ORDER_BUSINESS_API_USER"),
                password=_env("ORDER_BUSINESS_API_PASSWORD"),
                secret_key=_env("ORDER_BUSINESS_API_SECRET_KEY"),
            ),
            auth_mode=getenv("ORDER_BUSINESS_API_AUTH_MODE", "basic_query_secret"),
            user_param=getenv("ORDER_BUSINESS_API_USER_PARAM", "user"),
            secret_param=getenv("ORDER_BUSINESS_API_SECRET_PARAM", "secret_key"),
        ),
        fedex_api=ServiceEndpoint(
            base_url=getenv("FEDEX_API_BASE_URL"),
            credentials=ServiceCredentials(
                username=_env("FEDEX_API_USER"),
                password=_env("FEDEX_API_PASSWORD"),
                secret_key=_env("FEDEX_API_SECRET_KEY"),
            ),
            auth_mode=getenv("FEDEX_API_AUTH_MODE", "basic_query_secret"),
            user_param=getenv("FEDEX_API_USER_PARAM", "user"),
            secret_param=getenv("FEDEX_API_SECRET_PARAM", "secret_key"),
        ),
        freshdesk=FreshdeskEndpoint(
            base_url=_env("FRESHDESK_BASE_URL"),
            api_key=_env("FRESHDESK_API_KEY"),
        ),
    )


settings = load_settings()

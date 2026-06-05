from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse

from cs_orchestration.api.routes.enrichment import router as enrichment_router
from cs_orchestration.config.settings import Settings, settings
from cs_orchestration.ui import render_agent_preview


def _validate_production_settings(app_settings: Settings) -> None:
    if app_settings.app_env != "production":
        return
    if app_settings.inbound_api_key is None:
        raise RuntimeError("INBOUND_API_KEY is required when APP_ENV=production.")


def create_app(app_settings: Settings = settings) -> FastAPI:
    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        _validate_production_settings(app_settings)
        yield

    app = FastAPI(
        title=app_settings.app_name,
        docs_url="/docs" if app_settings.expose_docs else None,
        redoc_url="/redoc" if app_settings.expose_docs else None,
        openapi_url="/openapi.json" if app_settings.expose_docs else None,
        lifespan=lifespan,
    )
    app.include_router(enrichment_router)

    @app.get("/", response_class=HTMLResponse)
    def agent_preview() -> HTMLResponse:
        if app_settings.app_env == "production":
            raise HTTPException(status_code=404, detail="Not found.")
        return render_agent_preview(
            integration_mode=app_settings.integration_mode,
            dry_run=app_settings.dry_run,
        )

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/config/status")
    def config_status() -> dict[str, object]:
        if app_settings.app_env == "production":
            raise HTTPException(status_code=404, detail="Not found.")
        return {
            "app_env": app_settings.app_env,
            "integration_mode": app_settings.integration_mode,
            "dry_run": app_settings.dry_run,
            "expose_docs": app_settings.expose_docs,
            "expose_debug_errors": app_settings.expose_debug_errors,
            "inbound_api": {
                "api_key_configured": app_settings.inbound_api_key is not None,
                "header_name": app_settings.inbound_api_key_header,
            },
            "order_business_api": {
                "base_url_configured": app_settings.order_business_api.base_url is not None,
                "user_configured": app_settings.order_business_api.credentials.username is not None,
                "password_configured": app_settings.order_business_api.credentials.password is not None,
                "secret_key_configured": app_settings.order_business_api.credentials.secret_key is not None,
                "auth_mode": app_settings.order_business_api.auth_mode,
            },
            "fedex_api": {
                "base_url_configured": app_settings.fedex_api.base_url is not None,
                "user_configured": app_settings.fedex_api.credentials.username is not None,
                "password_configured": app_settings.fedex_api.credentials.password is not None,
                "secret_key_configured": app_settings.fedex_api.credentials.secret_key is not None,
                "auth_mode": app_settings.fedex_api.auth_mode,
            },
            "freshdesk": {
                "base_url_configured": app_settings.freshdesk.base_url is not None,
                "api_key_configured": app_settings.freshdesk.api_key is not None,
            },
        }

    return app


app = create_app()

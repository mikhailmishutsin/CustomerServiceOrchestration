from fastapi import FastAPI

from cs_orchestration.api.routes.enrichment import router as enrichment_router
from cs_orchestration.config.settings import settings


app = FastAPI(title=settings.app_name)
app.include_router(enrichment_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}

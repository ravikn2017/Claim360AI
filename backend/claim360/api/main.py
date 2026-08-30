from fastapi import FastAPI
from fastapi.responses import JSONResponse

from claim360.config import get_settings
from claim360.db import ping_database

app = FastAPI(title="Claim360 API")


@app.get("/health")
def health() -> dict[str, str]:
    get_settings()
    return {"status": "ok"}


@app.get("/ready")
def ready() -> JSONResponse:
    try:
        ping_database()
    except Exception:
        return JSONResponse(status_code=503, content={"status": "unavailable", "database": "error"})
    return JSONResponse(status_code=200, content={"status": "ok", "database": "ok"})

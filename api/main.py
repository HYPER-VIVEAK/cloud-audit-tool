"""FastAPI gateway for the cloud audit tool."""

import asyncio
import logging
from typing import List

import pymysql
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .db import ensure_auth_schema
from .mongo_store import ensure_scan_indexes
from .routes_auth import router as auth_router
from .routes_credentials import router as credentials_router
from .routes_resources import router as resources_router
from .routes_scan import router as scan_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("cloud-audit-api")


async def _startup_with_retries() -> None:
    last_error: Exception | None = None
    for _ in range(20):
        try:
            ensure_auth_schema()
            ensure_scan_indexes()
            return
        except pymysql.err.OperationalError as exc:
            last_error = exc
            logger.warning("Waiting for MySQL to become ready: %s", exc)
            await asyncio.sleep(2)
        except Exception as exc:
            # MongoDB can also be briefly unavailable during container cold start.
            last_error = exc
            logger.warning("Waiting for database services to become ready: %s", exc)
            await asyncio.sleep(2)

    if last_error:
        raise last_error


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name)

    # CORS
    allow_origins: List[str] = settings.cors_allow_origins or ["http://localhost:5173"]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth_router, prefix=settings.api_prefix)
    app.include_router(credentials_router, prefix=settings.api_prefix)
    app.include_router(scan_router, prefix=settings.api_prefix)
    app.include_router(resources_router, prefix=settings.api_prefix)

    @app.on_event("startup")
    async def startup() -> None:
        await _startup_with_retries()

    @app.get("/")
    async def root():
        return {"service": settings.app_name, "status": "ok"}

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)

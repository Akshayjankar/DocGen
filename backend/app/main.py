"""FastAPI app factory."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app import APP_NAME, __version__
from app.api.v1 import brand_kits, documents, formats, health, jobs, lint, logos, previews, themes
from app.config import get_settings
from app.deps import get_engine, limiter
from app.services.storage import get_storage


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    get_engine()
    get_storage()

    async def cleaner() -> None:
        while True:
            await asyncio.sleep(300)
            get_storage().cleanup_expired()

    task = asyncio.create_task(cleaner())
    yield
    task.cancel()


def create_app() -> FastAPI:
    settings = get_settings()
    docs_url = None if settings.env == "production" else "/docs"
    redoc_url = None if settings.env == "production" else "/redoc"
    openapi_url = None if settings.env == "production" else "/openapi.json"

    application = FastAPI(
        title=APP_NAME,
        version=__version__,
        lifespan=lifespan,
        docs_url=docs_url,
        redoc_url=redoc_url,
        openapi_url=openapi_url,
    )
    application.state.limiter = limiter
    application.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    application.add_middleware(SlowAPIMiddleware)
    # Allow localhost and 127.0.0.1 (browsers treat them as different origins)
    origins = {
        settings.frontend_origin,
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3003",
        "http://127.0.0.1:3003",
        "http://localhost:3004",
        "http://127.0.0.1:3004",
    }
    application.add_middleware(
        CORSMiddleware,
        allow_origins=sorted(o for o in origins if o),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    api = "/api/v1"
    application.include_router(health.router, prefix=api)
    application.include_router(themes.router, prefix=api)
    application.include_router(documents.router, prefix=api)
    application.include_router(jobs.router, prefix=api)
    application.include_router(brand_kits.router, prefix=api)
    application.include_router(lint.router, prefix=api)
    application.include_router(logos.router, prefix=api)
    application.include_router(previews.router, prefix=api)
    application.include_router(formats.router, prefix=api)

    def _frontend_base() -> str:
        return settings.frontend_origin.rstrip("/")

    def _to_frontend(path: str) -> RedirectResponse:
        base = _frontend_base()
        target = path if path.startswith("/") else f"/{path}"
        return RedirectResponse(url=f"{base}{target}", status_code=307)

    @application.get("/", include_in_schema=False)
    def root_redirect() -> RedirectResponse:
        return _to_frontend("/")

    @application.get("/studio", include_in_schema=False)
    @application.get("/studio/", include_in_schema=False)
    def studio_redirect() -> RedirectResponse:
        return _to_frontend("/studio")

    @application.get("/brand-kits", include_in_schema=False)
    @application.get("/library", include_in_schema=False)
    @application.get("/privacy", include_in_schema=False)
    def ui_path_redirect(request: Request) -> RedirectResponse:
        return _to_frontend(request.url.path.rstrip("/") or "/")

    @application.get("/api", include_in_schema=False)
    @application.get("/api/", include_in_schema=False)
    def api_index() -> JSONResponse:
        payload: dict[str, object] = {
            "app": APP_NAME,
            "version": __version__,
            "health": f"{api}/health",
            "frontend": _frontend_base(),
            "hint": (
                "This process is the API only. Open the Next.js app for UI "
                f"(e.g. {_frontend_base()}/studio)."
            ),
        }
        if docs_url:
            payload["docs"] = docs_url
        return JSONResponse(payload)

    @application.middleware("http")
    async def security_headers(request: Request, call_next):  # type: ignore[no-untyped-def]
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        return response

    @application.exception_handler(Exception)
    async def unhandled(_request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(status_code=500, content={"detail": str(exc)})

    return application


app = create_app()

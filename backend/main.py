"""Backend entry point: builds the FastAPI application and starts the server.

Run:
    python -m backend.main                       # uses HOST / PORT from .env
    uvicorn backend.main:build_default_app --factory --host 0.0.0.0 --port 8000

On startup the inference worker starts and loads the model in the
background, so the server answers right away. Questions sent before the
model is ready simply wait in the queue.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import router
from config.logging_setup import setup_logging
from config.settings import Settings, get_settings
from inference.factory import build_inference_service
from inference.service import InferenceService

logger = logging.getLogger(__name__)


def create_app(settings: Settings, service: InferenceService | None = None) -> FastAPI:
    """Build the app. Tests pass their own `service` (with a fake engine)."""
    service = service or build_inference_service(settings)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        service.start()
        logger.info("Backend ready on %s:%s", settings.server.host, settings.server.port)
        yield
        service.stop()

    app = FastAPI(title="Plateforme IA documentaire", version="0.1.0", lifespan=lifespan)
    app.state.settings = settings
    app.state.inference_service = service

    # Let the web interface (other port / domain) call the API
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.server.cors_origins,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )
    app.include_router(router)
    return app


def build_default_app() -> FastAPI:
    """App built from `.env`. Kept as a factory so importing this module has no side effect."""
    settings = get_settings()
    setup_logging(settings.log_level, settings.paths.logs_dir)
    return create_app(settings)


if __name__ == "__main__":
    import uvicorn

    server = get_settings().server
    # One worker process only: the model lives in memory, one copy per process
    uvicorn.run(build_default_app(), host=server.host, port=server.port, workers=1)

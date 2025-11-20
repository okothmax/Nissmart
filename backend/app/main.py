"""Application entrypoint for the Nissmart Ledger API."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router as api_router
from app.core.config import get_settings


def create_application() -> FastAPI:
    settings = get_settings()

    app = FastAPI(title=settings.app_name, debug=settings.debug)

    # Allow local dev and future admin dashboard origins
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router)

    return app


app = create_application()

import uuid

import logfire
import sentry_sdk
import uvicorn
from fastapi import APIRouter, FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.routing import APIRoute
from fastapi.openapi.utils import get_openapi
from pydantic import ValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.routes import auth, follow, health, meeting, user
from app.utils.config import settings
from app.utils.exceptions import (
    http_validation_error,
    request_validation_error,
    validation_error,
)


def create_app() -> FastAPI:
    init_sentry()

    app = FastAPI(
        title=settings.PROJECT_NAME,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        generate_unique_id_function=custom_generate_unique_id,
    )

    # Custom OpenAPI schema
    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema
        openapi_schema = get_openapi(
            title=app.title,
            version="3.0.2",
            summary="API schema for scheduling, managing, and interacting with social meetings",
            description=(
                "This API allows users to create, manage, and participate in meetings or social events.\n\n"
                "### Core Features:\n"
                "- User authentication and registration\n"
                "- Meeting creation, approval, rejection, and indexing\n"
                "- Participant management (add/remove participants, status updates)\n"
                "- Follow system to connect with other users\n\n"
                "Built using **FastAPI** for high performance and clean documentation."
            ),
            routes=app.routes,
        )
        openapi_schema["info"]["x-logo"] = {
            "url": "https://fastapi.tiangolo.com/img/logo-margin/logo-teal.png"
        }
        app.openapi_schema = openapi_schema
        return app.openapi_schema

    app.openapi = custom_openapi

    # Exception handlers
    app.add_exception_handler(StarletteHTTPException, http_validation_error)
    app.add_exception_handler(RequestValidationError, request_validation_error)
    app.add_exception_handler(ValidationError, validation_error)

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Routers
    app.include_router(create_api_router(), prefix=settings.API_V1_STR)

    # Observability
    init_logfire(app)

    return app


def custom_generate_unique_id(route: APIRoute) -> str:
    return f"{route.tags[0]}-{route.name}"


def init_sentry() -> None:
    if settings.SENTRY_DSN and settings.ENVIRONMENT != "development":
        sentry_sdk.init(
            dsn=str(settings.SENTRY_DSN),
            enable_tracing=True,
        )


def init_logfire(app: FastAPI) -> None:
    if settings.LOGFIRE_TOKEN and settings.ENVIRONMENT not in ["local", "development"]:
        try:
            logfire.configure()
            logfire.instrument_fastapi(app)
        except Exception as e:
            print(f"Warning: Failed to initialize Logfire: {e}")


def create_api_router() -> APIRouter:
    router = APIRouter()

    router.include_router(health.router, prefix="/health", tags=["health"])
    router.include_router(auth.router, prefix="/auth", tags=["auth"])
    router.include_router(user.router, prefix="/user", tags=["user"])
    router.include_router(follow.router, prefix="/follow", tags=["follow"])
    router.include_router(meeting.router, prefix="/meeting", tags=["meeting"])

    return router


if __name__ == "__main__":
    app = create_app()
    uvicorn.run(app, host="0.0.0.0", port=8000)


import os
import secrets
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from backend.app.core.database import engine
from backend.app.models.incident import Incident
from backend.app.models.telemetry import TelemetrySample

from backend.app.api.routes import router
from backend.app.api.telemetry import router as telemetry_router
from backend.app.api.investigation import (
    router as investigation_router,
)
from backend.app.api.auth import (
    router as auth_router,
    require_auth,
    auth_enabled,
)

load_dotenv()

ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
]


@asynccontextmanager
async def lifespan(app: FastAPI):

    if auth_enabled():
        password = os.getenv("NEXUS_ADMIN_PASSWORD", "")
        secret = os.getenv("NEXUS_SESSION_SECRET", "")

        if len(password) < 12:
            raise RuntimeError(
                "NEXUS_ADMIN_PASSWORD must contain "
                "at least 12 characters."
            )

        if len(secret) < 32:
            raise RuntimeError(
                "NEXUS_SESSION_SECRET must contain "
                "at least 32 characters."
            )

    # Existing database tables are not reset.
    TelemetrySample.__table__.create(
        bind=engine,
        checkfirst=True,
    )

    yield


app = FastAPI(
    title="NEXUS AI",
    description="AI Operations & Incident Intelligence Platform",
    version="0.5.0",
    lifespan=lifespan,
)

session_secret = os.getenv("NEXUS_SESSION_SECRET")

if not session_secret:
    # Temporary secret for development before authentication
    # is configured. Sessions won't survive process restarts.
    session_secret = secrets.token_urlsafe(48)

app.add_middleware(
    SessionMiddleware,
    secret_key=session_secret,
    session_cookie="nexus_session",
    max_age=3600,
    same_site="strict",
    https_only=(
        os.getenv("NEXUS_COOKIE_SECURE", "false").lower()
        == "true"
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

# Public authentication routes.
app.include_router(auth_router)

# Protected application APIs.
app.include_router(
    router,
    dependencies=[Depends(require_auth)],
)

app.include_router(
    telemetry_router,
    dependencies=[Depends(require_auth)],
)

app.include_router(
    investigation_router,
    dependencies=[Depends(require_auth)],
)


@app.get("/")
def root():
    return {
        "project": "NEXUS AI",
        "status": "operational",
        "version": "0.5.0",
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}


"""
NEXUS AI - Phase 9C
Single-admin authentication with login rate limiting.

Security:
- Signed HttpOnly session cookies (configured in main.py)
- Admin password verification
- Origin checks for state-changing requests
- 5 failed logins -> 60-second temporary lockout
- No password or secret logging

This rate limiter is process-local. Production deployments
should use a shared persistent rate-limit store.
"""

import os
import secrets
from datetime import datetime, timedelta, timezone
from threading import Lock
from urllib.parse import urlparse

from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

load_dotenv()

router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication"],
)

ALLOWED_ORIGINS = {
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
}

MAX_FAILED_ATTEMPTS = 5
LOCKOUT_SECONDS = 60
ATTEMPT_WINDOW_SECONDS = 300

_failed_attempts = {}
_attempts_lock = Lock()


class LoginRequest(BaseModel):
    password: str = Field(
        min_length=1,
        max_length=1024,
    )


def auth_enabled():
    return (
        os.getenv("NEXUS_AUTH_ENABLED", "false").lower()
        == "true"
    )


def utc_now():
    return datetime.now(timezone.utc)


def client_identifier(request: Request):
    """
    Use the directly connected client address.

    Do not trust X-Forwarded-For without a configured,
    trusted reverse proxy.
    """
    if request.client and request.client.host:
        return request.client.host

    return "unknown-client"


def validate_request_origin(request: Request):
    origin = request.headers.get("origin")

    if not origin:
        referer = request.headers.get("referer")

        if referer:
            parsed = urlparse(referer)

            if parsed.scheme and parsed.netloc:
                origin = (
                    f"{parsed.scheme}://{parsed.netloc}"
                )

    if origin not in ALLOWED_ORIGINS:
        raise HTTPException(
            status_code=403,
            detail="Untrusted or missing request origin.",
        )


def is_rate_limited(identifier):
    now = utc_now()

    with _attempts_lock:
        entry = _failed_attempts.get(identifier)

        if entry is None:
            return False

        blocked_until = entry.get("blocked_until")

        if blocked_until is not None:
            if now < blocked_until:
                return True

            _failed_attempts.pop(identifier, None)
            return False

        cutoff = now - timedelta(
            seconds=ATTEMPT_WINDOW_SECONDS
        )

        entry["failures"] = [
            timestamp
            for timestamp in entry["failures"]
            if timestamp >= cutoff
        ]

        if not entry["failures"]:
            _failed_attempts.pop(identifier, None)

        return False


def record_failed_login(identifier):
    now = utc_now()
    cutoff = now - timedelta(
        seconds=ATTEMPT_WINDOW_SECONDS
    )

    with _attempts_lock:
        entry = _failed_attempts.setdefault(
            identifier,
            {
                "failures": [],
                "blocked_until": None,
            },
        )

        entry["failures"] = [
            timestamp
            for timestamp in entry["failures"]
            if timestamp >= cutoff
        ]

        entry["failures"].append(now)

        if len(entry["failures"]) >= MAX_FAILED_ATTEMPTS:
            entry["blocked_until"] = (
                now + timedelta(seconds=LOCKOUT_SECONDS)
            )


def clear_failed_logins(identifier):
    with _attempts_lock:
        _failed_attempts.pop(identifier, None)


def require_auth(request: Request):
    if not auth_enabled():
        return True

    if not request.session.get("authenticated"):
        raise HTTPException(
            status_code=401,
            detail="Authentication required.",
        )

    if request.method not in {
        "GET",
        "HEAD",
        "OPTIONS",
    }:
        validate_request_origin(request)

    return True


@router.get("/me")
def current_user(request: Request):
    enabled = auth_enabled()

    authenticated = (
        bool(request.session.get("authenticated"))
        if enabled
        else False
    )

    return {
        "auth_enabled": enabled,
        "authenticated": authenticated,
        "role": "admin" if authenticated else None,
    }


@router.post("/login")
def login(payload: LoginRequest, request: Request):
    if not auth_enabled():
        raise HTTPException(
            status_code=409,
            detail="Authentication is disabled.",
        )

    validate_request_origin(request)

    identifier = client_identifier(request)

    if is_rate_limited(identifier):
        raise HTTPException(
            status_code=429,
            detail=(
                "Too many failed login attempts. "
                "Please try again later."
            ),
            headers={"Retry-After": str(LOCKOUT_SECONDS)},
        )

    configured_password = os.getenv(
        "NEXUS_ADMIN_PASSWORD", ""
    )

    # Never permit login with an empty configuration.
    if not configured_password:
        raise HTTPException(
            status_code=503,
            detail="Admin authentication is not configured.",
        )

    valid = secrets.compare_digest(
        payload.password.encode("utf-8"),
        configured_password.encode("utf-8"),
    )

    if not valid:
        record_failed_login(identifier)

        raise HTTPException(
            status_code=401,
            detail="Invalid admin password.",
        )

    clear_failed_logins(identifier)

    request.session.clear()
    request.session["authenticated"] = True

    return {
        "status": "LOGIN_SUCCESS",
        "role": "admin",
    }


@router.post("/logout")
def logout(request: Request):
    if auth_enabled():
        validate_request_origin(request)

    request.session.clear()

    return {
        "status": "LOGGED_OUT",
    }

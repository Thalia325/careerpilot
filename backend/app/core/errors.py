"""Centralized error response utilities for consistent API error handling.

All protected APIs should use these helpers so that:
- 401 responses carry error_code AUTH_REQUIRED or INVALID_CREDENTIALS
- 403 responses carry error_code INSUFFICIENT_ROLE or RESOURCE_FORBIDDEN
- Frontend callers can distinguish login-required vs no-permission from the payload
- Cross-role / cross-resource failures do NOT leak the existence of forbidden records
"""

from __future__ import annotations

from fastapi import HTTPException, status


# ---------------------------------------------------------------------------
# Error codes – exposed in the response payload so the frontend can branch
# ---------------------------------------------------------------------------

AUTH_REQUIRED = "AUTH_REQUIRED"
INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
INSUFFICIENT_ROLE = "INSUFFICIENT_ROLE"
RESOURCE_FORBIDDEN = "RESOURCE_FORBIDDEN"


# ---------------------------------------------------------------------------
# Helper to build a structured detail dict
# ---------------------------------------------------------------------------

def _detail(message: str, error_code: str) -> dict:
    return {"message": message, "error_code": error_code}


# ---------------------------------------------------------------------------
# Public factory functions
# ---------------------------------------------------------------------------

def raise_unauthorized(message: str = "请先登录") -> HTTPException:
    """401 – missing or malformed auth header."""
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=_detail(message, AUTH_REQUIRED),
        headers={"WWW-Authenticate": "Bearer"},
    )


def raise_invalid_credentials(message: str = "登录凭证无效或已过期") -> HTTPException:
    """401 – token present but invalid / expired / user not found."""
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=_detail(message, INVALID_CREDENTIALS),
        headers={"WWW-Authenticate": "Bearer"},
    )


def raise_insufficient_role(
    required_role: str | None = None,
    message: str | None = None,
) -> HTTPException:
    """403 – authenticated but wrong role for this endpoint."""
    if message is None:
        message = "权限不足，无法访问该资源"
    exc = HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=_detail(message, INSUFFICIENT_ROLE),
    )
    raise exc


def raise_resource_forbidden(message: str = "无权访问此资源") -> HTTPException:
    """403 – authenticated, correct role, but wrong owner / out of scope.

    The message is intentionally generic so it does NOT leak whether the
    target resource exists or belongs to another user.
    """
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=_detail(message, RESOURCE_FORBIDDEN),
    )


# ---------------------------------------------------------------------------
# Convenience: require_role checker
# ---------------------------------------------------------------------------

def require_role(user_role: str, *allowed: str) -> None:
    """Raise INSUFFICIENT_ROLE if *user_role* is not in *allowed*."""
    if user_role not in allowed:
        raise_insufficient_role()

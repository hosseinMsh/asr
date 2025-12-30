from dataclasses import dataclass
from enum import Enum
from typing import Any

from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import exception_handler as drf_exception_handler
from rest_framework.exceptions import (
    APIException,
    ValidationError,
    ParseError,
    NotAuthenticated,
    AuthenticationFailed,
    PermissionDenied,
    NotFound,
    Throttled,
)


# -----------------------------
# Error Model
# -----------------------------

class ErrorCategory(str, Enum):
    USER = "user"          # UI / human mistakes
    AUTH = "auth"          # auth / permission
    CLIENT = "client"      # request / contract
    TRANSIENT = "transient"  # retryable
    SERVER = "server"      # bugs / crashes


@dataclass(frozen=True)
class ErrorEnvelope:
    code: str
    message: str
    category: ErrorCategory
    status_code: int
    details: Any | None = None


# -----------------------------
# Response helper
# -----------------------------

def error_response(envelope: ErrorEnvelope) -> Response:
    payload = {
        "code": envelope.code,
        "message": envelope.message,
        "category": envelope.category,
    }
    if envelope.details is not None:
        payload["details"] = envelope.details

    return Response(payload, status=envelope.status_code)


# -----------------------------
# Exception Handler
# -----------------------------

def exception_handler(exc, context):
    response = drf_exception_handler(exc, context)

    # -------------------------
    # Unhandled exception
    # -------------------------
    if response is None:
        return error_response(
            ErrorEnvelope(
                code="SERVER_ERROR",
                message="Unexpected server error.",
                category=ErrorCategory.SERVER,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        )

    # -------------------------
    # Validation / Parse
    # -------------------------
    if isinstance(exc, (ValidationError, ParseError)):
        return error_response(
            ErrorEnvelope(
                code="INVALID_REQUEST",
                message="Invalid request data.",
                category=ErrorCategory.CLIENT,
                status_code=response.status_code,
                details=exc.detail if isinstance(exc, ValidationError) else None,
            )
        )

    # -------------------------
    # Authentication
    # -------------------------
    if isinstance(exc, NotAuthenticated):
        return error_response(
            ErrorEnvelope(
                code="UNAUTHENTICATED",
                message="Authentication credentials were not provided.",
                category=ErrorCategory.AUTH,
                status_code=response.status_code,
            )
        )

    if isinstance(exc, AuthenticationFailed):
        return error_response(
            ErrorEnvelope(
                code="AUTHENTICATION_FAILED",
                message=str(exc.detail),
                category=ErrorCategory.AUTH,
                status_code=response.status_code,
            )
        )

    if isinstance(exc, PermissionDenied):
        return error_response(
            ErrorEnvelope(
                code="FORBIDDEN",
                message="You do not have permission to perform this action.",
                category=ErrorCategory.AUTH,
                status_code=response.status_code,
            )
        )

    # -------------------------
    # Resource
    # -------------------------
    if isinstance(exc, NotFound):
        return error_response(
            ErrorEnvelope(
                code="NOT_FOUND",
                message="Requested resource was not found.",
                category=ErrorCategory.CLIENT,
                status_code=response.status_code,
            )
        )

    # -------------------------
    # Rate limit
    # -------------------------
    if isinstance(exc, Throttled):
        return error_response(
            ErrorEnvelope(
                code="RATE_LIMITED",
                message="Too many requests. Please try again later.",
                category=ErrorCategory.TRANSIENT,
                status_code=response.status_code,
            )
        )

    # -------------------------
    # Any other DRF exception
    # -------------------------
    if isinstance(exc, APIException):
        return error_response(
            ErrorEnvelope(
                code="REQUEST_FAILED",
                message=str(exc.detail),
                category=ErrorCategory.CLIENT,
                status_code=response.status_code,
            )
        )

    # -------------------------
    # Fallback
    # -------------------------
    return error_response(
        ErrorEnvelope(
            code="SERVER_ERROR",
            message="Unexpected server error.",
            category=ErrorCategory.SERVER,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
    )

from dataclasses import dataclass
from enum import Enum

from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import exception_handler as drf_exception_handler
from rest_framework.exceptions import (
    APIException,
    NotAuthenticated,
    PermissionDenied,
    ValidationError,
    NotFound,
    ParseError,
    Throttled,
)


class ErrorCategory(str, Enum):
    USER = "user"
    TRANSIENT = "transient"
    SERVER = "server"


@dataclass(frozen=True)
class ErrorEnvelope:
    code: str
    message: str
    category: ErrorCategory
    status_code: int


def error_response(code: str, message: str, status_code: int) -> Response:
    return Response({"code": code, "message": message}, status=status_code)


def exception_handler(exc, context):
    response = drf_exception_handler(exc, context)
    if response is None:
        envelope = ErrorEnvelope(
            code="SERVER_ERROR",
            message="Unexpected server error.",
            category=ErrorCategory.SERVER,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
        return error_response(envelope.code, envelope.message, envelope.status_code)

    if isinstance(exc, (ValidationError, ParseError)):
        envelope = ErrorEnvelope(
            code="INVALID_REQUEST",
            message="Invalid request.",
            category=ErrorCategory.USER,
            status_code=response.status_code,
        )
    elif isinstance(exc, NotAuthenticated):
        envelope = ErrorEnvelope(
            code="UNAUTHENTICATED",
            message="Authentication required.",
            category=ErrorCategory.USER,
            status_code=response.status_code,
        )
    elif isinstance(exc, PermissionDenied):
        envelope = ErrorEnvelope(
            code="FORBIDDEN",
            message="You do not have access to this resource.",
            category=ErrorCategory.USER,
            status_code=response.status_code,
        )
    elif isinstance(exc, NotFound):
        envelope = ErrorEnvelope(
            code="NOT_FOUND",
            message="Resource not found.",
            category=ErrorCategory.USER,
            status_code=response.status_code,
        )
    elif isinstance(exc, Throttled):
        envelope = ErrorEnvelope(
            code="RATE_LIMITED",
            message="Too many requests. Please try again later.",
            category=ErrorCategory.TRANSIENT,
            status_code=response.status_code,
        )
    elif isinstance(exc, APIException):
        envelope = ErrorEnvelope(
            code="REQUEST_FAILED",
            message="Request could not be processed.",
            category=ErrorCategory.SERVER,
            status_code=response.status_code,
        )
    else:
        envelope = ErrorEnvelope(
            code="SERVER_ERROR",
            message="Unexpected server error.",
            category=ErrorCategory.SERVER,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    return error_response(envelope.code, envelope.message, envelope.status_code)

"""Custom exception handling for AssetGuard API."""
import logging

from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import Http404
from rest_framework import status
from rest_framework.exceptions import (
    APIException,
    ValidationError as DRFValidationError,
)
from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Custom exception handler that normalizes all error responses
    into a consistent format.
    """
    # Convert Django ValidationError to DRF ValidationError
    if isinstance(exc, DjangoValidationError):
        if hasattr(exc, "message_dict"):
            exc = DRFValidationError(detail=exc.message_dict)
        else:
            exc = DRFValidationError(detail=exc.messages)

    response = exception_handler(exc, context)

    if response is not None:
        error_payload = {
            "status_code": response.status_code,
            "error": _get_error_type(response.status_code),
            "details": response.data,
        }
        response.data = error_payload
    else:
        # Unhandled exceptions
        logger.exception("Unhandled exception: %s", str(exc), extra={"context": context})
        response = Response(
            {
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "error": "Internal Server Error",
                "details": "An unexpected error occurred. Please try again later.",
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    return response


def _get_error_type(status_code):
    """Map HTTP status codes to human-readable error types."""
    error_types = {
        400: "Bad Request",
        401: "Unauthorized",
        403: "Forbidden",
        404: "Not Found",
        405: "Method Not Allowed",
        409: "Conflict",
        422: "Unprocessable Entity",
        429: "Too Many Requests",
        500: "Internal Server Error",
    }
    return error_types.get(status_code, "Error")


class AssetNotAvailableError(APIException):
    """Raised when an asset is not available for assignment."""

    status_code = status.HTTP_409_CONFLICT
    default_detail = "This asset is not available for assignment."
    default_code = "asset_not_available"


class LicenseLimitExceededError(APIException):
    """Raised when license seat limit is exceeded."""

    status_code = status.HTTP_409_CONFLICT
    default_detail = "No available seats for this license."
    default_code = "license_limit_exceeded"


class DepreciationCalculationError(APIException):
    """Raised when depreciation calculation fails."""

    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    default_detail = "Unable to calculate depreciation with the given parameters."
    default_code = "depreciation_error"

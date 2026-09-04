from rest_framework.exceptions import APIException
from rest_framework.views import (
    exception_handler as drf_exception_handler,
)


class ServiceUnavailable(APIException):
    """
    API exception used when a required service is unavailable.
    """

    status_code = 503
    default_detail = "Service temporarily unavailable."
    default_code = "service_unavailable"


ERROR_CODES = {
    401: "authentication_required",
    403: "permission_denied",
    404: "not_found",
    405: "method_not_allowed",
    503: "service_unavailable",
}


DEFAULT_MESSAGES = {
    401: "Authentication is required.",
    403: "Permission denied.",
    404: "Resource not found.",
    405: "HTTP method not allowed.",
    503: "Service temporarily unavailable.",
}


def extract_detail_message(
    data,
    default_message,
):
    """
    Extract a human-readable message from a DRF error response.
    """
    if isinstance(
        data,
        dict,
    ):
        detail = data.get(
            "detail"
        )

        if detail is not None:
            return str(
                detail
            )

    if isinstance(
        data,
        list,
    ) and data:
        return str(
            data[0]
        )

    return default_message


def api_exception_handler(
    exc,
    context,
):
    """
    Convert DRF exceptions to a consistent API error format.

    Validation errors keep their field-level details while other
    API errors expose a stable code and human-readable message.
    """
    response = drf_exception_handler(
        exc,
        context,
    )

    if response is None:
        return None

    if response.status_code == 400:
        original_data = (
            response.data
        )

        response.data = {
            "error": {
                "code": "validation_error",
                "message": (
                    "Request validation failed."
                ),
                "details": original_data,
            }
        }

        return response

    error_code = ERROR_CODES.get(
        response.status_code,
        "api_error",
    )

    default_message = (
        DEFAULT_MESSAGES.get(
            response.status_code,
            "The API request failed.",
        )
    )

    message = extract_detail_message(
        response.data,
        default_message,
    )

    response.data = {
        "error": {
            "code": error_code,
            "message": message,
        }
    }

    return response
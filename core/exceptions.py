from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
import logging

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None:
        error_detail = response.data

        # Flatten list errors to a single string when possible
        if isinstance(error_detail, list) and len(error_detail) == 1:
            error_detail = error_detail[0]

        response.data = {
            "success": False,
            "status_code": response.status_code,
            "error": error_detail,
        }
    else:
        logger.exception("Unhandled exception", exc_info=exc)
        response = Response(
            {
                "success": False,
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "error": "An unexpected error occurred. Please try again later.",
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    return response

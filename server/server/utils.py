"""Utility helpers for DRF error normalization."""

from django.conf import settings
from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    """Normalize DRF exceptions without leaking internals."""
    response = exception_handler(exc, context)
    if response is None:
        return response

    detail = response.data
    if isinstance(detail, dict):
        payload = {"error": detail}
    elif isinstance(detail, list):
        payload = {"error": {"non_field_errors": detail}}
    else:
        payload = {"error": {"detail": str(detail)}}

    if settings.DEBUG:
        payload["debug"] = {"exception_type": exc.__class__.__name__}

    response.data = payload
    return response

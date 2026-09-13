"""Project-wide DRF exception handling.

DRF's default handler leaves unhandled exceptions to Django, which returns an
HTML 500. This wrapper keeps every API response JSON and logs the failure.
"""

import logging

from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404
from rest_framework import exceptions, status
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler

logger = logging.getLogger(__name__)


def api_exception_handler(exc, context):
    # A model's DoesNotExist escaping a view is a 404, not a 500.
    if isinstance(exc, ObjectDoesNotExist) and not isinstance(exc, Http404):
        exc = exceptions.NotFound()

    response = drf_exception_handler(exc, context)

    if response is None:
        view = context.get("view")
        logger.exception("Unhandled exception in %s", view.__class__.__name__)
        return Response(
            {"detail": "A server error occurred."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    return response

"""Covers the shared exception handler and the Celery email task."""

import pytest
from django.core import mail
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import exceptions

from apps.common.exceptions import api_exception_handler
from apps.common.tasks import send_email_task


class _View:
    pass


def _context():
    return {"view": _View()}


def test_model_does_not_exist_becomes_a_404():
    response = api_exception_handler(ObjectDoesNotExist("gone"), _context())

    assert response.status_code == 404


def test_drf_errors_pass_straight_through():
    response = api_exception_handler(exceptions.PermissionDenied(), _context())

    assert response.status_code == 403


def test_an_unhandled_exception_becomes_a_json_500():
    """Django would otherwise return an HTML error page from an API route."""
    response = api_exception_handler(RuntimeError("boom"), _context())

    assert response.status_code == 500
    assert response.data == {"detail": "A server error occurred."}


@pytest.mark.django_db
def test_send_email_task_delivers(settings):
    settings.MAILERS = {
        "default": {"BACKEND": "django.core.mail.backends.locmem.EmailBackend"}
    }
    mail.outbox.clear()

    sent = send_email_task(
        subject="Viewing request",
        body="Can I view the villa?",
        recipient_list=["agent@example.com"],
        reply_to=["ada@example.com"],
    )

    assert sent == 1
    message = mail.outbox[0]
    assert message.subject == "Viewing request"
    assert message.to == ["agent@example.com"]
    assert message.reply_to == ["ada@example.com"]


@pytest.mark.django_db
def test_send_email_task_attaches_an_html_alternative(settings):
    settings.MAILERS = {
        "default": {"BACKEND": "django.core.mail.backends.locmem.EmailBackend"}
    }
    mail.outbox.clear()

    send_email_task(
        subject="Welcome",
        body="Plain text",
        recipient_list=["agent@example.com"],
        html_body="<p>Rich text</p>",
    )

    assert mail.outbox[0].alternatives[0][0] == "<p>Rich text</p>"


@pytest.mark.django_db
def test_send_email_task_falls_back_to_default_from_email(settings):
    settings.MAILERS = {
        "default": {"BACKEND": "django.core.mail.backends.locmem.EmailBackend"}
    }
    mail.outbox.clear()

    send_email_task(
        subject="Welcome", body="Hello", recipient_list=["agent@example.com"]
    )

    assert mail.outbox[0].from_email == settings.DEFAULT_FROM_EMAIL

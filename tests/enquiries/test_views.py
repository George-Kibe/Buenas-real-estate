"""Covers the enquiry endpoint, which now queues mail via Celery."""

from unittest.mock import patch

import pytest
from rest_framework.test import APIClient

from apps.enquiries.models import Enquiry


@pytest.fixture
def client():
    return APIClient()


VALID = {
    "name": "Ada Smith",
    "email": "ada@example.com",
    "subject": "Viewing request",
    "message": "Can I view the villa on Saturday?",
}


@patch("apps.enquiries.views.send_email_task.delay")
def test_enquiry_is_saved_and_queued(delay, db, client):
    response = client.post("/api/v1/enquiries/", VALID, format="json")

    assert response.status_code == 201
    assert Enquiry.objects.count() == 1

    delay.assert_called_once()
    kwargs = delay.call_args.kwargs
    assert kwargs["reply_to"] == ["ada@example.com"]
    assert "Viewing request" in kwargs["subject"]


@patch("apps.enquiries.views.send_email_task.delay")
def test_invalid_enquiry_is_rejected(delay, db, client):
    response = client.post(
        "/api/v1/enquiries/", {**VALID, "email": "not-an-email"}, format="json"
    )

    assert response.status_code == 400
    assert "email" in response.data
    assert Enquiry.objects.count() == 0
    delay.assert_not_called()

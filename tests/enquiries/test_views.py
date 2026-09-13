"""API coverage for apps/enquiries/urls.py."""

from unittest.mock import patch

from django.urls import reverse

from apps.enquiries.models import Enquiry

ENQUIRY_URL = reverse("send-enquiry")

VALID = {
    "name": "Ada Smith",
    "email": "ada@example.com",
    "subject": "Viewing request",
    "message": "Can I view the villa on Saturday?",
}


@patch("apps.enquiries.views.send_email_task.delay")
def test_enquiry_is_saved_and_queued(delay, db, api_client):
    response = api_client.post(ENQUIRY_URL, VALID, format="json")

    assert response.status_code == 201
    assert Enquiry.objects.count() == 1

    delay.assert_called_once()
    kwargs = delay.call_args.kwargs
    assert kwargs["reply_to"] == ["ada@example.com"]
    assert "Viewing request" in kwargs["subject"]
    assert "Can I view the villa" in kwargs["body"]


@patch("apps.enquiries.views.send_email_task.delay")
def test_enquiry_is_public(delay, db, api_client):
    """No Authorization header — the contact form must work for visitors."""
    assert api_client.post(ENQUIRY_URL, VALID, format="json").status_code == 201


@patch("apps.enquiries.views.send_email_task.delay")
def test_enquiry_accepts_an_optional_phone_number(delay, db, api_client):
    response = api_client.post(
        ENQUIRY_URL, {**VALID, "phone_number": "+254712345678"}, format="json"
    )

    assert response.status_code == 201
    assert str(Enquiry.objects.get().phone_number) == "+254712345678"


@patch("apps.enquiries.views.send_email_task.delay")
def test_invalid_email_is_rejected(delay, db, api_client):
    response = api_client.post(
        ENQUIRY_URL, {**VALID, "email": "not-an-email"}, format="json"
    )

    assert response.status_code == 400
    assert "email" in response.data
    assert Enquiry.objects.count() == 0
    delay.assert_not_called()


@patch("apps.enquiries.views.send_email_task.delay")
def test_blank_message_is_rejected(delay, db, api_client):
    response = api_client.post(ENQUIRY_URL, {**VALID, "message": "   "}, format="json")

    assert response.status_code == 400
    delay.assert_not_called()


@patch("apps.enquiries.views.send_email_task.delay")
def test_missing_subject_is_rejected(delay, db, api_client):
    payload = {key: value for key, value in VALID.items() if key != "subject"}

    response = api_client.post(ENQUIRY_URL, payload, format="json")

    assert response.status_code == 400
    delay.assert_not_called()


@patch("apps.enquiries.views.send_email_task.delay")
def test_bad_phone_number_is_rejected(delay, db, api_client):
    response = api_client.post(
        ENQUIRY_URL, {**VALID, "phone_number": "12"}, format="json"
    )

    assert response.status_code == 400


def test_enquiry_str_is_the_email(db, enquiry_factory):
    enquiry = enquiry_factory.create(email="ada@example.com")
    assert str(enquiry) == "ada@example.com"

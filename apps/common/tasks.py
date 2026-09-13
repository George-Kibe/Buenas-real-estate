"""Shared Celery tasks.

Replaces django-celery-email, which is incompatible with the MAILERS API
introduced in Django 6.1.
"""

import logging

from celery import shared_task
from django.conf import settings
from django.core.mail import EmailMultiAlternatives

logger = logging.getLogger(__name__)


@shared_task(
    name="common.send_email",
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def send_email_task(
    self,
    subject,
    body,
    recipient_list,
    from_email=None,
    reply_to=None,
    html_body=None,
):
    """Send one email off the request thread.

    Arguments are plain JSON-serialisable types so the task survives a broker
    round trip.
    """
    message = EmailMultiAlternatives(
        subject=subject,
        body=body,
        from_email=from_email or settings.DEFAULT_FROM_EMAIL,
        to=list(recipient_list),
        reply_to=list(reply_to) if reply_to else None,
    )
    if html_body:
        message.attach_alternative(html_body, "text/html")

    sent = message.send()
    logger.info("Sent %s email(s) to %s", sent, recipient_list)
    return sent

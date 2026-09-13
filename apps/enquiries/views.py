import logging

from django.conf import settings
from rest_framework import permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from apps.common.tasks import send_email_task

from .serializers import EnquirySerializer

logger = logging.getLogger(__name__)


@api_view(["POST"])
@permission_classes([permissions.AllowAny])
def send_enquiry_email(request):
    serializer = EnquirySerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    enquiry = serializer.save()

    # Queued rather than sent inline so a slow SMTP server can't stall the API.
    send_email_task.delay(
        subject=f"[Enquiry] {enquiry.subject}",
        body=f"From: {enquiry.name} <{enquiry.email}>\n\n{enquiry.message}",
        recipient_list=[settings.DEFAULT_FROM_EMAIL],
        reply_to=[enquiry.email],
    )
    logger.info("Enquiry received from %s", enquiry.email)

    return Response(
        {"success": "Your Enquiry was successfully submitted"},
        status=status.HTTP_201_CREATED,
    )

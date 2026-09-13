import logging

from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .exceptions import NotYourProfile, ProfileNotFound
from .models import Profile
from .pagination import ProfilePagination
from .renderers import ProfileJSONRenderer
from .serializers import ProfileSerializer, UpdateProfileSerializer

logger = logging.getLogger(__name__)


def _agent_queryset(**filters):
    # prefetch_related on the reviews keeps ProfileSerializer.get_reviews from
    # issuing one query per agent.
    return (
        Profile.objects.select_related("user")
        .prefetch_related("agent_review__rater", "agent_review__agent__user")
        .filter(**filters)
        .order_by("-rating", "user__username")
    )


class AgentListAPIView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ProfileSerializer
    pagination_class = ProfilePagination

    def get_queryset(self):
        return _agent_queryset(is_agent=True)


class TopAgentsListAPIView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ProfileSerializer
    pagination_class = ProfilePagination

    def get_queryset(self):
        return _agent_queryset(top_agent=True)


class GetProfileAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    renderer_classes = [ProfileJSONRenderer]
    serializer_class = ProfileSerializer

    def get(self, request):
        try:
            user_profile = Profile.objects.select_related("user").get(user=request.user)
        except Profile.DoesNotExist:
            raise ProfileNotFound

        serializer = ProfileSerializer(user_profile, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class UpdateProfileAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    renderer_classes = [ProfileJSONRenderer]
    serializer_class = UpdateProfileSerializer

    def patch(self, request, username):
        try:
            profile = Profile.objects.select_related("user").get(
                user__username=username
            )
        except Profile.DoesNotExist:
            raise ProfileNotFound

        if profile.user != request.user:
            raise NotYourProfile

        serializer = UpdateProfileSerializer(
            instance=profile, data=request.data, partial=True
        )
        # Without raise_exception invalid input was silently saved.
        serializer.is_valid(raise_exception=True)
        serializer.save()
        logger.info("Profile updated for %s", username)
        return Response(serializer.data, status=status.HTTP_200_OK)

import logging

from django.db.models import Avg, Count
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from apps.profiles.exceptions import ProfileNotFound
from apps.profiles.models import Profile

from .models import Rating
from .serializers import CreateRatingSerializer, RatingSerializer

logger = logging.getLogger(__name__)


@extend_schema(
    request=CreateRatingSerializer,
    responses={
        201: RatingSerializer,
        400: OpenApiResponse(description="Invalid rating, or already reviewed"),
        401: OpenApiResponse(description="Authentication required"),
        403: OpenApiResponse(description="You cannot rate yourself"),
        404: OpenApiResponse(description="No such agent"),
    },
    summary="Review an agent",
    tags=["ratings"],
)
@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def create_agent_review(request, profile_id):
    try:
        agent_profile = Profile.objects.select_related("user").get(
            id=profile_id, is_agent=True
        )
    except Profile.DoesNotExist:
        raise ProfileNotFound

    if agent_profile.user == request.user:
        return Response(
            {"detail": "You can't rate yourself."}, status=status.HTTP_403_FORBIDDEN
        )

    # One review per rater per agent; the model enforces this too.
    if Rating.objects.filter(rater=request.user, agent=agent_profile).exists():
        return Response(
            {"detail": "You have already reviewed this agent."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    serializer = CreateRatingSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    review = serializer.save(rater=request.user, agent=agent_profile)

    _refresh_agent_rating(agent_profile)
    logger.info("%s reviewed agent %s", request.user.username, agent_profile.id)

    return Response(RatingSerializer(review).data, status=status.HTTP_201_CREATED)


def _refresh_agent_rating(agent_profile):
    """Recompute the cached aggregate in the database rather than in Python."""
    stats = Rating.objects.filter(agent=agent_profile).aggregate(
        average=Avg("rating"), total=Count("pkid")
    )
    agent_profile.num_reviews = stats["total"] or 0
    agent_profile.rating = (
        round(stats["average"], 2) if stats["average"] is not None else None
    )
    agent_profile.save(update_fields=["num_reviews", "rating"])

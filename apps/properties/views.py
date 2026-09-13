import logging

import django_filters
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import filters, generics, permissions, status
from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from .exceptions import PropertyNotFound
from .models import Property, PropertyViews
from .pagination import PropertyPagination
from .serializers import (
    PropertyCreateSerializer,
    PropertyImageUploadSerializer,
    PropertySearchSerializer,
    PropertySerializer,
    PropertyViewSerializer,
)

logger = logging.getLogger(__name__)

NOT_OWNER = "You do not have permission to modify a property that isn't yours."


class PropertyFilter(django_filters.FilterSet):
    advert_type = django_filters.CharFilter(
        field_name="advert_type", lookup_expr="iexact"
    )
    property_type = django_filters.CharFilter(
        field_name="property_type", lookup_expr="iexact"
    )

    price = django_filters.NumberFilter()
    price__gt = django_filters.NumberFilter(field_name="price", lookup_expr="gt")
    price__lt = django_filters.NumberFilter(field_name="price", lookup_expr="lt")

    class Meta:
        model = Property
        fields = ["advert_type", "property_type", "price"]


def _get_property_or_404(slug):
    try:
        return Property.objects.get(slug=slug)
    except Property.DoesNotExist:
        raise PropertyNotFound


class ListAllPropertiesAPIView(generics.ListAPIView):
    """Public listing. select_related avoids an N+1 on user/profile."""

    permission_classes = [permissions.AllowAny]
    serializer_class = PropertySerializer
    queryset = (
        Property.objects.select_related("user", "user__profile")
        .all()
        .order_by("-created_at")
    )
    pagination_class = PropertyPagination
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_class = PropertyFilter
    search_fields = ["country", "city", "title"]
    ordering_fields = ["created_at", "price", "views"]


class ListAgentsPropertiesAPIView(generics.ListAPIView):
    """The signed-in user's own listings."""

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PropertySerializer
    pagination_class = PropertyPagination
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_class = PropertyFilter
    search_fields = ["country", "city", "title"]
    ordering_fields = ["created_at", "price", "views"]

    # Read by drf-spectacular during schema generation; get_queryset wins
    # at request time.
    queryset = Property.objects.none()

    def get_queryset(self):
        return (
            Property.objects.select_related("user", "user__profile")
            .filter(user=self.request.user)
            .order_by("-created_at")
        )


class PropertyViewsAPIView(generics.ListAPIView):
    """Per-IP view records for the requesting user's own listings."""

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PropertyViewSerializer
    pagination_class = PropertyPagination

    queryset = PropertyViews.objects.none()  # for schema generation only

    def get_queryset(self):
        return PropertyViews.objects.filter(property__user=self.request.user).order_by(
            "-created_at"
        )


class PropertyDetailView(APIView):
    """Public detail view. The first request from a given IP bumps the counter."""

    permission_classes = [permissions.AllowAny]
    serializer_class = PropertySerializer

    @extend_schema(
        responses={
            200: PropertySerializer,
            404: OpenApiResponse(description="No such property"),
        },
        summary="Property detail (increments the view counter)",
        tags=["properties"],
    )
    def get(self, request, slug):
        property = _get_property_or_404(slug)

        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0].strip()
        else:
            ip = request.META.get("REMOTE_ADDR")

        if ip and not PropertyViews.objects.filter(property=property, ip=ip).exists():
            PropertyViews.objects.create(property=property, ip=ip)
            # update_fields keeps this from clobbering a concurrent edit.
            property.views += 1
            property.save(update_fields=["views"])

        serializer = PropertySerializer(property, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema(
    request=PropertyCreateSerializer,
    responses={
        201: PropertyCreateSerializer,
        400: OpenApiResponse(description="Validation error"),
        401: OpenApiResponse(description="Authentication required"),
    },
    summary="Create a property",
    description="The owner is taken from the access token, never the body.",
    tags=["properties"],
)
@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def create_property_api_view(request):
    serializer = PropertyCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    # The owner comes from the token, never from the request body.
    property = serializer.save(user=request.user)
    logger.info("Property %s created by %s", property.slug, request.user.username)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@extend_schema(
    request=PropertyCreateSerializer,
    responses={
        200: PropertyCreateSerializer,
        400: OpenApiResponse(description="Validation error"),
        401: OpenApiResponse(description="Authentication required"),
        403: OpenApiResponse(description="Not your property"),
        404: OpenApiResponse(description="No such property"),
    },
    summary="Update a property you own",
    tags=["properties"],
)
@api_view(["PUT", "PATCH"])
@permission_classes([permissions.IsAuthenticated])
def update_property_api_view(request, slug):
    property = _get_property_or_404(slug)

    if property.user != request.user:
        return Response({"detail": NOT_OWNER}, status=status.HTTP_403_FORBIDDEN)

    serializer = PropertyCreateSerializer(
        property, data=request.data, partial=request.method == "PATCH"
    )
    serializer.is_valid(raise_exception=True)
    serializer.save()
    logger.info("Property %s updated by %s", property.slug, request.user.username)
    return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema(
    request=None,
    responses={
        204: OpenApiResponse(description="Deleted"),
        401: OpenApiResponse(description="Authentication required"),
        403: OpenApiResponse(description="Not your property"),
        404: OpenApiResponse(description="No such property"),
    },
    summary="Delete a property you own",
    tags=["properties"],
)
@api_view(["DELETE"])
@permission_classes([permissions.IsAuthenticated])
def delete_property_api_view(request, slug):
    property = _get_property_or_404(slug)

    if property.user != request.user:
        return Response({"detail": NOT_OWNER}, status=status.HTTP_403_FORBIDDEN)

    property.delete()
    logger.info("Property %s deleted by %s", slug, request.user.username)
    return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(
    request={"multipart/form-data": PropertyImageUploadSerializer},
    responses={
        200: OpenApiResponse(description="Image(s) uploaded"),
        400: OpenApiResponse(description="Not a valid image"),
        401: OpenApiResponse(description="Authentication required"),
        403: OpenApiResponse(description="Not your property"),
        404: OpenApiResponse(description="No such property"),
    },
    summary="Upload photos for a property you own",
    tags=["properties"],
)
@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def upload_property_image(request, slug):
    """Replace one or more photos on a listing you own.

    Only the fields present in the request are touched, so posting just
    `photo2` leaves the cover photo alone.
    """
    property = _get_property_or_404(slug)

    if property.user != request.user:
        return Response({"detail": NOT_OWNER}, status=status.HTTP_403_FORBIDDEN)

    serializer = PropertyImageUploadSerializer(
        property, data=request.data, partial=True
    )
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(
        {"success": "Image(s) uploaded"},
        status=status.HTTP_200_OK,
    )


class PropertySearchAPIView(APIView):
    """Structured search over published listings."""

    permission_classes = [permissions.AllowAny]
    serializer_class = PropertySearchSerializer

    @extend_schema(
        request=PropertySearchSerializer,
        responses={200: PropertySerializer(many=True)},
        summary="Structured search over published listings",
        tags=["properties"],
    )
    def post(self, request):
        search = PropertySearchSerializer(data=request.data)
        search.is_valid(raise_exception=True)

        queryset = search.filter_queryset(
            Property.objects.select_related("user", "user__profile").filter(
                published_status=True
            )
        )
        return Response(
            PropertySerializer(queryset, many=True, context={"request": request}).data,
            status=status.HTTP_200_OK,
        )

from django_countries.serializer_fields import CountryField
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from .models import Property, PropertyViews


def _file_url(file_field):
    """ImageField.url raises ValueError when no file is set."""
    if not file_field:
        return None
    try:
        return file_field.url
    except ValueError:
        return None


class PropertySerializer(serializers.ModelSerializer):
    """Read representation. Every computed field here is read-only, so this
    serializer must never be used to write — see PropertyCreateSerializer."""

    user = serializers.CharField(source="user.username", read_only=True)
    final_property_price = serializers.FloatField(read_only=True)
    country = CountryField(name_only=True, read_only=True)
    cover_photo = serializers.SerializerMethodField()
    profile_photo = serializers.SerializerMethodField()
    photo1 = serializers.SerializerMethodField()
    photo2 = serializers.SerializerMethodField()
    photo3 = serializers.SerializerMethodField()
    photo4 = serializers.SerializerMethodField()

    class Meta:
        model = Property
        fields = [
            "id",
            "user",
            "profile_photo",
            "title",
            "slug",
            "ref_code",
            "description",
            "country",
            "city",
            "postal_code",
            "street_address",
            "property_number",
            "price",
            "tax",
            "final_property_price",
            "plot_area",
            "total_floors",
            "bedrooms",
            "bathrooms",
            "advert_type",
            "property_type",
            "cover_photo",
            "photo1",
            "photo2",
            "photo3",
            "photo4",
            "published_status",
            "views",
            "created_at",
        ]
        read_only_fields = fields

    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_cover_photo(self, obj):
        return _file_url(obj.cover_photo)

    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_photo1(self, obj):
        return _file_url(obj.photo1)

    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_photo2(self, obj):
        return _file_url(obj.photo2)

    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_photo3(self, obj):
        return _file_url(obj.photo3)

    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_photo4(self, obj):
        return _file_url(obj.photo4)

    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_profile_photo(self, obj):
        profile = getattr(obj.user, "profile", None)
        return _file_url(profile.profile_photo) if profile else None


class PropertyCreateSerializer(serializers.ModelSerializer):
    """Write representation.

    `user`, `slug`, `ref_code` and `views` are deliberately excluded: they are
    server-owned, and accepting them from the client would let a caller
    reassign ownership or forge a reference code.
    """

    country = CountryField(name_only=True, required=False)

    class Meta:
        model = Property
        fields = [
            "id",
            "title",
            "description",
            "country",
            "city",
            "postal_code",
            "street_address",
            "property_number",
            "price",
            "tax",
            "plot_area",
            "total_floors",
            "bedrooms",
            "bathrooms",
            "advert_type",
            "property_type",
            "cover_photo",
            "photo1",
            "photo2",
            "photo3",
            "photo4",
            "published_status",
            "slug",
            "ref_code",
            "views",
            "created_at",
        ]
        read_only_fields = ["id", "slug", "ref_code", "views", "created_at"]
        # Non-negative bounds come from the model's MinValueValidators, which
        # ModelSerializer copies onto the generated fields.


class PropertyViewSerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertyViews
        fields = ["id", "ip", "property", "created_at"]
        read_only_fields = fields


PRICE_BRACKETS = [
    "0+",
    "50,000+",
    "100,000+",
    "200,000+",
    "400,000+",
    "600,000+",
    "Any",
]
ROOM_BRACKETS = ["0+", "1+", "2+", "3+", "4+", "5+", "Any"]


class PropertySearchSerializer(serializers.Serializer):
    """Validates the POST body of the structured search endpoint.

    The client sends bracketed strings ("100,000+", "3+"); anything else is
    rejected here rather than raising a KeyError inside the view.
    """

    PRICE_CHOICES = {
        "0+": 0,
        "50,000+": 50000,
        "100,000+": 100000,
        "200,000+": 200000,
        "400,000+": 400000,
        "600,000+": 600000,
        "Any": None,
    }
    ROOM_CHOICES = {"0+": 0, "1+": 1, "2+": 2, "3+": 3, "4+": 4, "5+": 5, "Any": None}

    advert_type = serializers.ChoiceField(
        choices=Property.AdvertType.choices, required=False, allow_blank=True
    )
    property_type = serializers.ChoiceField(
        choices=Property.PropertyType.choices, required=False, allow_blank=True
    )
    price = serializers.ChoiceField(
        choices=PRICE_BRACKETS, required=False, allow_blank=True
    )
    bedrooms = serializers.ChoiceField(
        choices=ROOM_BRACKETS, required=False, allow_blank=True
    )
    bathrooms = serializers.ChoiceField(
        choices=ROOM_BRACKETS, required=False, allow_blank=True
    )
    catch_phrase = serializers.CharField(
        required=False, allow_blank=True, max_length=255
    )

    def filter_queryset(self, queryset):
        data = self.validated_data

        if data.get("advert_type"):
            queryset = queryset.filter(advert_type__iexact=data["advert_type"])
        if data.get("property_type"):
            queryset = queryset.filter(property_type__iexact=data["property_type"])

        price = self.PRICE_CHOICES.get(data.get("price"))
        if price is not None:
            queryset = queryset.filter(price__gte=price)

        bedrooms = self.ROOM_CHOICES.get(data.get("bedrooms"))
        if bedrooms is not None:
            queryset = queryset.filter(bedrooms__gte=bedrooms)

        bathrooms = self.ROOM_CHOICES.get(data.get("bathrooms"))
        if bathrooms is not None:
            queryset = queryset.filter(bathrooms__gte=bathrooms)

        if data.get("catch_phrase"):
            queryset = queryset.filter(description__icontains=data["catch_phrase"])

        return queryset


class PropertyImageUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Property
        fields = ["cover_photo", "photo1", "photo2", "photo3", "photo4"]

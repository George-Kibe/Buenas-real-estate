"""API coverage for every route in apps/properties/urls.py."""

from decimal import Decimal
from io import BytesIO

import pytest
from django.urls import reverse
from PIL import Image
from rest_framework.test import APIClient

from apps.properties.models import Property, PropertyViews

ALL_URL = reverse("get-all-properties")
AGENTS_URL = reverse("agent-properties")
VIEWS_URL = reverse("property-views")
CREATE_URL = reverse("property-create")
SEARCH_URL = reverse("property-search")


def detail_url(slug):
    return reverse("property-details", args=[slug])


def update_url(slug):
    return reverse("update-property", args=[slug])


def delete_url(slug):
    return reverse("delete-property", args=[slug])


def upload_url(slug):
    return reverse("property-upload-image", args=[slug])


VALID_PAYLOAD = {
    "title": "lakeside villa in naivasha",
    "description": "a calm three bedroom home by the lake",
    "country": "KE",
    "city": "Naivasha",
    "price": "9500000.00",
    "bedrooms": 3,
    "bathrooms": "2.50",
    "plot_area": "450.00",
    "total_floors": 2,
    "advert_type": "For Sale",
    "property_type": "House",
    "published_status": True,
}


def _image_file(name="photo.jpg"):
    buffer = BytesIO()
    Image.new("RGB", (4, 4), "green").save(buffer, format="JPEG")
    buffer.seek(0)
    buffer.name = name
    return buffer


# --------------------------------------------------------------------------
# GET /properties/all/
# --------------------------------------------------------------------------


def test_list_is_public(db, api_client, listing):
    response = api_client.get(ALL_URL)

    assert response.status_code == 200
    assert response.data["count"] == 1
    assert response.data["results"][0]["slug"] == listing.slug


def test_list_is_paginated(db, api_client, property_factory):
    property_factory.create_batch(15)

    response = api_client.get(ALL_URL)

    assert response.data["count"] == 15
    assert len(response.data["results"]) == 12
    assert response.data["next"] is not None


def test_list_respects_page_size(db, api_client, property_factory):
    property_factory.create_batch(5)

    response = api_client.get(ALL_URL, {"page_size": 2})

    assert len(response.data["results"]) == 2


def test_list_filters_by_advert_type(db, api_client, property_factory):
    property_factory.create(advert_type=Property.AdvertType.FOR_SALE)
    property_factory.create(advert_type=Property.AdvertType.FOR_RENT)

    response = api_client.get(ALL_URL, {"advert_type": "For Rent"})

    assert response.data["count"] == 1
    assert response.data["results"][0]["advert_type"] == "For Rent"


def test_list_filters_by_property_type(db, api_client, property_factory):
    property_factory.create(property_type=Property.PropertyType.HOUSE)
    property_factory.create(property_type=Property.PropertyType.OFFICE)

    response = api_client.get(ALL_URL, {"property_type": "Office"})

    assert response.data["count"] == 1


def test_list_filters_by_price_range(db, api_client, property_factory):
    property_factory.create(price=Decimal("1000000.00"))
    property_factory.create(price=Decimal("9000000.00"))

    response = api_client.get(ALL_URL, {"price__lt": "5000000"})

    assert response.data["count"] == 1
    assert Decimal(response.data["results"][0]["price"]) == Decimal("1000000.00")


def test_list_search_matches_city(db, api_client, property_factory):
    property_factory.create(city="Naivasha")
    property_factory.create(city="Mombasa")

    response = api_client.get(ALL_URL, {"search": "Naivasha"})

    assert response.data["count"] == 1


def test_list_ordering_by_price(db, api_client, property_factory):
    property_factory.create(price=Decimal("500000.00"))
    property_factory.create(price=Decimal("100000.00"))

    response = api_client.get(ALL_URL, {"ordering": "price"})

    prices = [Decimal(row["price"]) for row in response.data["results"]]
    assert prices == sorted(prices)


def test_list_serialises_photo_urls(db, api_client, listing):
    response = api_client.get(ALL_URL)
    row = response.data["results"][0]

    assert row["cover_photo"].endswith("house_sample.jpg")
    assert row["profile_photo"].endswith("profile_default.png")


def test_list_handles_a_cleared_photo(db, api_client, listing):
    # ImageField.url raises ValueError when no file is set.
    listing.cover_photo = ""
    listing.save()

    response = api_client.get(ALL_URL)

    assert response.status_code == 200
    assert response.data["results"][0]["cover_photo"] is None


# --------------------------------------------------------------------------
# GET /properties/agents/
# --------------------------------------------------------------------------


def test_agent_listings_require_auth(db, api_client, listing):
    response = api_client.get(AGENTS_URL)
    assert response.status_code == 401


def test_agent_listings_return_only_your_own(
    db, auth_client, other_user, listing, property_factory
):
    property_factory.create(user=other_user)

    response = auth_client.get(AGENTS_URL)

    assert response.data["count"] == 1
    assert response.data["results"][0]["slug"] == listing.slug


# --------------------------------------------------------------------------
# GET /properties/views/
# --------------------------------------------------------------------------


def test_property_views_require_auth(db, api_client):
    assert api_client.get(VIEWS_URL).status_code == 401


def test_property_views_scoped_to_your_listings(
    db, auth_client, listing, other_user, property_factory
):
    PropertyViews.objects.create(property=listing, ip="10.0.0.1")
    PropertyViews.objects.create(
        property=property_factory.create(user=other_user), ip="10.0.0.2"
    )

    response = auth_client.get(VIEWS_URL)

    assert response.data["count"] == 1
    assert response.data["results"][0]["ip"] == "10.0.0.1"


# --------------------------------------------------------------------------
# GET /properties/details/<slug>/
# --------------------------------------------------------------------------


def test_detail_is_public(db, api_client, listing):
    response = api_client.get(detail_url(listing.slug))

    assert response.status_code == 200
    assert response.data["ref_code"] == listing.ref_code


def test_detail_unknown_slug_returns_404(db, api_client):
    response = api_client.get(detail_url("no-such-listing"))

    assert response.status_code == 404
    assert "does not exist" in response.data["detail"]


def test_detail_increments_views_once_per_ip(db, api_client, listing):
    api_client.get(detail_url(listing.slug), REMOTE_ADDR="203.0.113.5")
    api_client.get(detail_url(listing.slug), REMOTE_ADDR="203.0.113.5")

    listing.refresh_from_db()
    assert listing.views == 1
    assert PropertyViews.objects.filter(property=listing).count() == 1


def test_detail_counts_distinct_ips_separately(db, api_client, listing):
    api_client.get(detail_url(listing.slug), REMOTE_ADDR="203.0.113.5")
    api_client.get(detail_url(listing.slug), REMOTE_ADDR="203.0.113.9")

    listing.refresh_from_db()
    assert listing.views == 2


def test_detail_prefers_x_forwarded_for(db, api_client, listing):
    api_client.get(
        detail_url(listing.slug),
        REMOTE_ADDR="10.0.0.1",
        HTTP_X_FORWARDED_FOR="198.51.100.7, 10.0.0.1",
    )

    assert PropertyViews.objects.filter(property=listing, ip="198.51.100.7").exists()


# --------------------------------------------------------------------------
# POST /properties/create/
# --------------------------------------------------------------------------


def test_create_requires_auth(db, api_client):
    assert api_client.post(CREATE_URL, VALID_PAYLOAD, format="json").status_code == 401


def test_create_returns_201_and_assigns_owner(db, auth_client, base_user):
    response = auth_client.post(CREATE_URL, VALID_PAYLOAD, format="json")

    assert response.status_code == 201
    created = Property.objects.get(slug=response.data["slug"])
    assert created.user == base_user
    assert created.title == "Lakeside Villa In Naivasha"


def test_create_accepts_a_realistic_kenyan_price(db, auth_client):
    response = auth_client.post(
        CREATE_URL, {**VALID_PAYLOAD, "price": "125000000.00"}, format="json"
    )

    assert response.status_code == 201


def test_create_ignores_a_user_supplied_owner(db, auth_client, base_user, other_user):
    """Mass assignment guard: `user` is not a writable field."""
    response = auth_client.post(
        CREATE_URL, {**VALID_PAYLOAD, "user": other_user.pkid}, format="json"
    )

    assert response.status_code == 201
    assert Property.objects.get(slug=response.data["slug"]).user == base_user


def test_create_ignores_a_user_supplied_slug_and_ref_code(db, auth_client):
    response = auth_client.post(
        CREATE_URL,
        {**VALID_PAYLOAD, "slug": "hijacked", "ref_code": "FORGED0001", "views": 999},
        format="json",
    )

    assert response.status_code == 201
    assert response.data["slug"] == "lakeside-villa-in-naivasha"
    assert response.data["ref_code"] != "FORGED0001"
    assert response.data["views"] == 0


def test_create_defaults_country_when_omitted(db, auth_client):
    payload = {key: value for key, value in VALID_PAYLOAD.items() if key != "country"}

    response = auth_client.post(CREATE_URL, payload, format="json")

    assert response.status_code == 201


def test_create_rejects_a_missing_title(db, auth_client):
    payload = {key: value for key, value in VALID_PAYLOAD.items() if key != "title"}

    response = auth_client.post(CREATE_URL, payload, format="json")

    assert response.status_code == 400
    assert "title" in response.data


def test_create_rejects_a_negative_price(db, auth_client):
    response = auth_client.post(
        CREATE_URL, {**VALID_PAYLOAD, "price": "-10.00"}, format="json"
    )

    assert response.status_code == 400
    assert "price" in response.data


def test_create_rejects_negative_bedrooms(db, auth_client):
    response = auth_client.post(
        CREATE_URL, {**VALID_PAYLOAD, "bedrooms": -1}, format="json"
    )

    assert response.status_code == 400
    assert "bedrooms" in response.data


def test_create_rejects_an_unknown_advert_type(db, auth_client):
    response = auth_client.post(
        CREATE_URL, {**VALID_PAYLOAD, "advert_type": "For Barter"}, format="json"
    )

    assert response.status_code == 400


# --------------------------------------------------------------------------
# PUT / PATCH /properties/update/<slug>/
# --------------------------------------------------------------------------


def test_update_requires_auth(db, api_client, listing):
    response = api_client.patch(
        update_url(listing.slug), {"city": "Nakuru"}, format="json"
    )
    assert response.status_code == 401


def test_update_unknown_slug_returns_404(db, auth_client):
    response = auth_client.patch(
        update_url("no-such-listing"), {"city": "Nakuru"}, format="json"
    )
    assert response.status_code == 404


def test_patch_persists_the_change(db, auth_client, listing):
    response = auth_client.patch(
        update_url(listing.slug), {"city": "Nakuru"}, format="json"
    )

    assert response.status_code == 200
    listing.refresh_from_db()
    assert listing.city == "Nakuru"


def test_put_persists_the_change(db, auth_client, listing):
    response = auth_client.put(
        update_url(listing.slug), {**VALID_PAYLOAD, "city": "Kisumu"}, format="json"
    )

    assert response.status_code == 200
    listing.refresh_from_db()
    assert listing.city == "Kisumu"


def test_update_is_blocked_for_non_owners(db, other_client, listing):
    response = other_client.patch(
        update_url(listing.slug), {"city": "Nakuru"}, format="json"
    )

    assert response.status_code == 403
    listing.refresh_from_db()
    assert listing.city != "Nakuru"


def test_update_cannot_transfer_ownership(db, auth_client, listing, other_user):
    auth_client.patch(
        update_url(listing.slug), {"user": other_user.pkid}, format="json"
    )

    listing.refresh_from_db()
    assert listing.user != other_user


def test_update_rejects_invalid_data(db, auth_client, listing):
    response = auth_client.patch(
        update_url(listing.slug), {"price": "-5.00"}, format="json"
    )

    assert response.status_code == 400


# --------------------------------------------------------------------------
# DELETE /properties/delete/<slug>/
# --------------------------------------------------------------------------


def test_delete_requires_auth(db, api_client, listing):
    assert api_client.delete(delete_url(listing.slug)).status_code == 401


def test_delete_removes_the_listing(db, auth_client, listing):
    response = auth_client.delete(delete_url(listing.slug))

    assert response.status_code == 204
    assert not Property.objects.filter(pkid=listing.pkid).exists()


def test_delete_is_blocked_for_non_owners(db, other_client, listing):
    response = other_client.delete(delete_url(listing.slug))

    assert response.status_code == 403
    assert Property.objects.filter(pkid=listing.pkid).exists()


def test_delete_unknown_slug_returns_404(db, auth_client):
    assert auth_client.delete(delete_url("no-such-listing")).status_code == 404


# --------------------------------------------------------------------------
# POST /properties/upload-image/<slug>/
# --------------------------------------------------------------------------


def test_upload_image_requires_auth(db, api_client, listing):
    response = api_client.post(
        upload_url(listing.slug), {"photo1": _image_file()}, format="multipart"
    )
    assert response.status_code == 401


def test_upload_image_replaces_only_the_supplied_field(db, auth_client, listing):
    original_cover = listing.cover_photo.name

    response = auth_client.post(
        upload_url(listing.slug), {"photo1": _image_file()}, format="multipart"
    )

    assert response.status_code == 200
    listing.refresh_from_db()
    assert listing.cover_photo.name == original_cover
    assert "photo" in listing.photo1.name


def test_upload_image_is_blocked_for_non_owners(db, other_client, listing):
    response = other_client.post(
        upload_url(listing.slug), {"photo1": _image_file()}, format="multipart"
    )

    assert response.status_code == 403


def test_upload_image_unknown_slug_returns_404(db, auth_client):
    response = auth_client.post(
        upload_url("no-such-listing"), {"photo1": _image_file()}, format="multipart"
    )
    assert response.status_code == 404


def test_upload_image_rejects_a_non_image(db, auth_client, listing):
    bogus = BytesIO(b"definitely not an image")
    bogus.name = "notes.txt"

    response = auth_client.post(
        upload_url(listing.slug), {"photo1": bogus}, format="multipart"
    )

    assert response.status_code == 400


# --------------------------------------------------------------------------
# POST /properties/search/
# --------------------------------------------------------------------------


def test_search_is_public(db, api_client, listing):
    response = api_client.post(SEARCH_URL, {}, format="json")

    assert response.status_code == 200
    assert len(response.data) == 1


def test_search_excludes_unpublished_listings(db, api_client, property_factory):
    property_factory.create(published_status=False)

    response = api_client.post(SEARCH_URL, {}, format="json")

    assert response.data == []


def test_search_filters_by_advert_and_property_type(db, api_client, property_factory):
    property_factory.create(
        advert_type=Property.AdvertType.FOR_RENT,
        property_type=Property.PropertyType.APARTMENT,
    )
    property_factory.create(
        advert_type=Property.AdvertType.FOR_SALE,
        property_type=Property.PropertyType.HOUSE,
    )

    response = api_client.post(
        SEARCH_URL,
        {"advert_type": "For Rent", "property_type": "Apartment"},
        format="json",
    )

    assert len(response.data) == 1


def test_search_applies_the_price_bracket(db, api_client, property_factory):
    property_factory.create(price=Decimal("40000.00"))
    property_factory.create(price=Decimal("250000.00"))

    response = api_client.post(SEARCH_URL, {"price": "100,000+"}, format="json")

    assert len(response.data) == 1


def test_search_any_price_matches_everything(db, api_client, property_factory):
    property_factory.create(price=Decimal("1.00"))
    property_factory.create(price=Decimal("900000.00"))

    response = api_client.post(SEARCH_URL, {"price": "Any"}, format="json")

    assert len(response.data) == 2


def test_search_applies_room_brackets(db, api_client, property_factory):
    property_factory.create(bedrooms=1, bathrooms=Decimal("1.00"))
    property_factory.create(bedrooms=4, bathrooms=Decimal("3.00"))

    response = api_client.post(
        SEARCH_URL, {"bedrooms": "3+", "bathrooms": "2+"}, format="json"
    )

    assert len(response.data) == 1


def test_search_matches_the_catch_phrase(db, api_client, property_factory):
    property_factory.create(description="Quiet home with a sunny garden")
    property_factory.create(description="Busy downtown office block")

    response = api_client.post(SEARCH_URL, {"catch_phrase": "garden"}, format="json")

    assert len(response.data) == 1


@pytest.mark.parametrize(
    "payload",
    [
        {"advert_type": "For Barter"},
        {"price": "1,000,000,000+"},
        {"bedrooms": "twelve"},
    ],
)
def test_search_rejects_unknown_values(db, api_client, payload):
    """These used to raise KeyError and return a 500."""
    response = api_client.post(SEARCH_URL, payload, format="json")

    assert response.status_code == 400


def test_search_missing_body_is_not_a_server_error(db, api_client):
    response = APIClient().post(SEARCH_URL, {}, format="json")

    assert response.status_code == 200


def test_photo_url_helper_survives_a_broken_storage():
    """ImageField.url raises ValueError for a file the storage cannot resolve."""
    from apps.properties.serializers import _file_url

    class _Broken:
        def __bool__(self):
            return True

        @property
        def url(self):
            raise ValueError("no file associated")

    assert _file_url(_Broken()) is None
    assert _file_url(None) is None

"""Covers the slug/ref_code generation that replaced django-autoslug."""

from decimal import Decimal

from apps.properties.models import Property, PropertyViews


def test_property_str(listing):
    assert str(listing) == listing.title


def test_title_is_title_cased(db, property_factory):
    new_property = property_factory.create(title="a lovely lakeside villa")
    assert new_property.title == "A Lovely Lakeside Villa"


def test_slug_is_derived_from_title(db, property_factory):
    new_property = property_factory.create(title="Lakeside Villa In Naivasha")
    assert new_property.slug == "lakeside-villa-in-naivasha"


def test_duplicate_titles_get_distinct_slugs(db, property_factory):
    first = property_factory.create(title="Lakeside Villa")
    second = property_factory.create(title="Lakeside Villa")
    assert first.slug == "lakeside-villa"
    assert second.slug == "lakeside-villa-2"
    assert first.slug != second.slug


def test_slug_follows_a_renamed_title(db, property_factory):
    new_property = property_factory.create(title="Old Name")
    new_property.title = "Brand New Name"
    new_property.save()
    assert new_property.slug == "brand-new-name"


def test_ref_code_is_assigned_once(db, property_factory):
    new_property = property_factory.create()
    original = new_property.ref_code
    assert len(original) == 10

    new_property.city = "Mombasa"
    new_property.save()
    new_property.refresh_from_db()
    # The reference code is what agents quote, so it must survive an edit.
    assert new_property.ref_code == original


def test_final_property_price_includes_tax(db, property_factory):
    new_property = property_factory.create(price=Decimal("1000"), tax=Decimal("0.15"))
    assert new_property.final_property_price == 1150.0


def test_published_manager_excludes_drafts(db, property_factory):
    property_factory.create(published_status=True)
    property_factory.create(published_status=False)

    assert Property.published.count() == 1
    assert Property.objects.count() == 2


def test_property_views_str(db, listing):
    view = PropertyViews.objects.create(property=listing, ip="203.0.113.5")

    assert str(view) == f"Total views on - {listing.title} is - {listing.views} view(s)"


def test_slug_falls_back_when_the_title_has_no_word_characters(db, property_factory):
    new_property = property_factory.create(title="!!! ???")

    assert new_property.slug.startswith("property")

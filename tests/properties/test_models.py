"""Covers the slug/ref_code generation that replaced django-autoslug."""

from decimal import Decimal


def test_property_str(property):
    assert str(property) == property.title


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

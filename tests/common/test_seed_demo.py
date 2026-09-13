"""Covers the seed_demo management command the API collection relies on."""

from io import StringIO

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError

from apps.properties.models import Property

User = get_user_model()


@pytest.fixture(autouse=True)
def _debug_on(settings):
    """Django's test runner forces DEBUG off, which the command refuses to run
    under. Opt back in for everything except the guard test itself."""
    settings.DEBUG = True


def _run():
    out = StringIO()
    call_command("seed_demo", stdout=out)
    return out.getvalue()


def test_creates_an_activated_demo_user(db):
    output = _run()

    demo = User.objects.get(email="asmith@example.com")
    assert demo.is_active is True
    assert demo.check_password("Str0ngPassw0rd!42")
    assert "asmith@example.com" in output


def test_creates_an_agent_with_a_listing(db):
    _run()

    agent = User.objects.get(email="agent@example.com")
    assert agent.profile.is_agent is True
    assert agent.profile.top_agent is True
    assert Property.objects.filter(user=agent).count() == 1


def test_prints_the_ids_the_collection_needs(db):
    output = _run()

    agent = User.objects.get(email="agent@example.com")
    listing = Property.objects.get(user=agent)
    assert str(agent.profile.id) in output
    assert listing.slug in output


def test_is_idempotent(db):
    _run()
    _run()

    assert User.objects.filter(email="asmith@example.com").count() == 1
    assert Property.objects.count() == 1


def test_resets_the_password_on_a_second_run(db):
    _run()
    demo = User.objects.get(email="asmith@example.com")
    demo.set_password("something-else")
    demo.is_active = False
    demo.save()

    _run()

    demo.refresh_from_db()
    assert demo.is_active is True
    assert demo.check_password("Str0ngPassw0rd!42")


def test_accepts_a_custom_password(db):
    call_command("seed_demo", "--password", "Cust0mPass!99", stdout=StringIO())

    demo = User.objects.get(email="asmith@example.com")
    assert demo.check_password("Cust0mPass!99")


def test_refuses_to_run_in_production(db, settings):
    """A command that sets a known password must never run with DEBUG off."""
    settings.DEBUG = False  # overrides the autouse fixture above

    with pytest.raises(CommandError, match="refuses to run"):
        call_command("seed_demo", stdout=StringIO())

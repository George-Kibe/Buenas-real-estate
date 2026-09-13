import pytest
from django.core.cache import cache
from pytest_factoryboy import register
from rest_framework.test import APIClient

from tests.factories import (
    EnquiryFactory,
    ProfileFactory,
    PropertyFactory,
    RatingFactory,
    UserFactory,
)

register(EnquiryFactory)
register(ProfileFactory)
register(PropertyFactory)
register(RatingFactory)
register(UserFactory)


@pytest.fixture(autouse=True)
def _clear_throttle_cache():
    """DRF throttling counts per-IP in the default cache, which outlives a
    single test. Clearing it keeps a long suite from tripping the anon rate."""
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def base_user(db, user_factory):
    return user_factory.create()


@pytest.fixture
def super_user(db, user_factory):
    return user_factory.create(is_staff=True, is_superuser=True)


@pytest.fixture
def profile(db, profile_factory):
    return profile_factory.create()


@pytest.fixture
def listing(db, property_factory, base_user):
    """One published property owned by `base_user`."""
    return property_factory.create(user=base_user)


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def auth_client(api_client, base_user):
    """An APIClient carrying a real JWT for `base_user`."""
    api_client.force_authenticate(user=base_user)
    return api_client


@pytest.fixture
def other_user(db, user_factory):
    return user_factory.create()


@pytest.fixture
def other_client(api_client, other_user):
    client = APIClient()
    client.force_authenticate(user=other_user)
    return client


@pytest.fixture
def agent_profile(db, user_factory):
    """A user whose auto-created profile is flagged as an agent."""
    user = user_factory.create()
    agent = user.profile
    agent.is_agent = True
    agent.save()
    return agent

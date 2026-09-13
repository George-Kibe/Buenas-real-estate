"""API coverage for the djoser auth routes and the schema endpoints."""

from django.contrib.auth import get_user_model
from django.urls import reverse

User = get_user_model()

REGISTER_URL = "/api/v1/auth/users/"
LOGIN_URL = "/api/v1/auth/jwt/create/"
REFRESH_URL = "/api/v1/auth/jwt/refresh/"
VERIFY_URL = "/api/v1/auth/jwt/verify/"
ME_URL = "/api/v1/auth/users/me/"

PASSWORD = "Str0ngPassw0rd!42"

REGISTRATION = {
    "username": "asmith",
    "email": "asmith@example.com",
    "first_name": "Ada",
    "last_name": "Smith",
    "password": PASSWORD,
    "re_password": PASSWORD,
}


def _active_user(user_factory, **kwargs):
    user = user_factory.create(**kwargs)
    user.set_password(PASSWORD)
    user.is_active = True
    user.save()
    return user


# --------------------------------------------------------------------------
# Registration
# --------------------------------------------------------------------------


def test_register_creates_a_user(db, api_client):
    response = api_client.post(REGISTER_URL, REGISTRATION, format="json")

    assert response.status_code == 201
    assert User.objects.filter(email="asmith@example.com").exists()


def test_register_creates_the_profile_via_signal(db, api_client):
    api_client.post(REGISTER_URL, REGISTRATION, format="json")

    user = User.objects.get(email="asmith@example.com")
    assert user.profile is not None
    assert user.profile.country.code == "KE"


def test_register_rejects_mismatched_passwords(db, api_client):
    response = api_client.post(
        REGISTER_URL, {**REGISTRATION, "re_password": "Different!42"}, format="json"
    )

    assert response.status_code == 400
    assert not User.objects.filter(email="asmith@example.com").exists()


def test_register_rejects_a_duplicate_email(db, api_client, user_factory):
    user_factory.create(email="asmith@example.com")

    response = api_client.post(REGISTER_URL, REGISTRATION, format="json")

    assert response.status_code == 400
    assert "email" in response.data


def test_register_rejects_a_weak_password(db, api_client):
    response = api_client.post(
        REGISTER_URL,
        {**REGISTRATION, "password": "12345678", "re_password": "12345678"},
        format="json",
    )

    assert response.status_code == 400


def test_register_never_echoes_the_password(db, api_client):
    response = api_client.post(REGISTER_URL, REGISTRATION, format="json")

    assert "password" not in response.data


# --------------------------------------------------------------------------
# JWT
# --------------------------------------------------------------------------


def test_login_returns_a_token_pair(db, api_client, user_factory):
    user = _active_user(user_factory)

    response = api_client.post(
        LOGIN_URL, {"email": user.email, "password": PASSWORD}, format="json"
    )

    assert response.status_code == 200
    assert "access" in response.data
    assert "refresh" in response.data


def test_login_rejects_a_wrong_password(db, api_client, user_factory):
    user = _active_user(user_factory)

    response = api_client.post(
        LOGIN_URL, {"email": user.email, "password": "wrong"}, format="json"
    )

    assert response.status_code == 401


def test_login_rejects_an_inactive_account(db, api_client, user_factory):
    user = _active_user(user_factory)
    user.is_active = False
    user.save()

    response = api_client.post(
        LOGIN_URL, {"email": user.email, "password": PASSWORD}, format="json"
    )

    assert response.status_code == 401


def test_refresh_issues_a_new_access_token(db, api_client, user_factory):
    user = _active_user(user_factory)
    tokens = api_client.post(
        LOGIN_URL, {"email": user.email, "password": PASSWORD}, format="json"
    ).data

    response = api_client.post(
        REFRESH_URL, {"refresh": tokens["refresh"]}, format="json"
    )

    assert response.status_code == 200
    assert "access" in response.data


def test_refresh_rejects_a_bogus_token(db, api_client):
    response = api_client.post(REFRESH_URL, {"refresh": "not-a-token"}, format="json")
    assert response.status_code == 401


def test_verify_accepts_a_live_token(db, api_client, user_factory):
    user = _active_user(user_factory)
    tokens = api_client.post(
        LOGIN_URL, {"email": user.email, "password": PASSWORD}, format="json"
    ).data

    response = api_client.post(VERIFY_URL, {"token": tokens["access"]}, format="json")

    assert response.status_code == 200


# --------------------------------------------------------------------------
# GET /auth/users/me/ — this is UserSerializer, which was broken
# --------------------------------------------------------------------------


def test_me_requires_auth(db, api_client):
    assert api_client.get(ME_URL).status_code == 401


def test_me_works_with_a_real_bearer_token(db, api_client, user_factory):
    user = _active_user(user_factory)
    tokens = api_client.post(
        LOGIN_URL, {"email": user.email, "password": PASSWORD}, format="json"
    ).data
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")

    response = api_client.get(ME_URL)

    assert response.status_code == 200
    assert response.data["email"] == user.email


def test_me_exposes_the_profile_fields(db, auth_client, base_user):
    """UserSerializer referenced a non-existent `top_seller`, sourced `city`
    from `profile.country`, and called `to_representaion`."""
    response = auth_client.get(ME_URL)

    assert response.status_code == 200
    assert response.data["top_agent"] is False
    assert response.data["city"] == base_user.profile.city
    # name_only, matching PropertySerializer and ProfileSerializer.
    assert response.data["country"] == "Kenya"
    assert response.data["full_name"] == (
        f"{base_user.first_name.title()} {base_user.last_name.title()}"
    )


def test_me_flags_superusers(db, api_client, user_factory):
    admin = _active_user(user_factory, is_superuser=True, is_staff=True)
    api_client.force_authenticate(user=admin)

    response = api_client.get(ME_URL)

    assert response.data["admin"] is True


def test_me_does_not_flag_ordinary_users(db, auth_client):
    assert "admin" not in auth_client.get(ME_URL).data


# --------------------------------------------------------------------------
# Schema / docs
# --------------------------------------------------------------------------


def test_openapi_schema_is_public_and_valid(db, api_client):
    response = api_client.get(reverse("schema"))

    assert response.status_code == 200
    assert response.data["info"]["title"] == "Buenas Real Estate API"
    assert "/api/v1/properties/all/" in response.data["paths"]


def test_swagger_ui_renders(db, api_client):
    assert api_client.get(reverse("swagger-ui")).status_code == 200

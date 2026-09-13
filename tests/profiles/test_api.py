"""API coverage for apps/profiles/urls.py."""

from django.urls import reverse

ME_URL = reverse("get_profile")
AGENTS_URL = reverse("all-agents")
TOP_AGENTS_URL = reverse("top-agents")


def update_url(username):
    return reverse("update_profile", args=[username])


# --------------------------------------------------------------------------
# GET /profile/me/
# --------------------------------------------------------------------------


def test_me_requires_auth(db, api_client):
    assert api_client.get(ME_URL).status_code == 401


def test_me_returns_the_wrapped_profile(db, auth_client, base_user):
    response = auth_client.get(ME_URL)

    assert response.status_code == 200
    # apps/profiles/renderers.py namespaces the payload at render time, so the
    # wrapper is only visible in the rendered body, not in response.data.
    body = response.json()
    assert "Profile" in body
    assert body["Profile"]["username"] == base_user.username


def test_me_country_uses_the_iso_code_default(db, auth_client):
    response = auth_client.get(ME_URL)

    # The model default used to be "Kenya", which serialised to "".
    assert response.json()["Profile"]["country"] == "Kenya"


def test_me_includes_reviews(db, auth_client, base_user, rating_factory, user_factory):
    agent = base_user.profile
    agent.is_agent = True
    agent.save()
    rating_factory.create(agent=agent, rater=user_factory.create(), rating=5)

    response = auth_client.get(ME_URL)

    reviews = response.json()["Profile"]["reviews"]
    assert len(reviews) == 1
    assert reviews[0]["rating"] == 5


def test_me_error_body_is_not_wrapped(db, api_client):
    """A 401 must stay readable; it used to come back as {"Profile": {...}}."""
    response = api_client.get(ME_URL)

    body = response.json()
    assert "Profile" not in body
    assert "detail" in body


def test_me_404s_when_the_profile_is_missing(db, auth_client, base_user):
    base_user.profile.delete()

    response = auth_client.get(ME_URL)

    assert response.status_code == 404


# --------------------------------------------------------------------------
# PATCH /profile/update/<username>/
# --------------------------------------------------------------------------


def test_update_requires_auth(db, api_client, base_user):
    response = api_client.patch(
        update_url(base_user.username), {"city": "Nakuru"}, format="json"
    )
    assert response.status_code == 401


def test_update_persists_your_own_profile(db, auth_client, base_user):
    response = auth_client.patch(
        update_url(base_user.username),
        {"city": "Nakuru", "about_me": "Agent in the Rift Valley"},
        format="json",
    )

    assert response.status_code == 200
    base_user.profile.refresh_from_db()
    assert base_user.profile.city == "Nakuru"
    assert base_user.profile.about_me == "Agent in the Rift Valley"


def test_update_is_blocked_for_other_users(db, other_client, base_user):
    response = other_client.patch(
        update_url(base_user.username), {"city": "Nakuru"}, format="json"
    )

    assert response.status_code == 403
    base_user.profile.refresh_from_db()
    assert base_user.profile.city != "Nakuru"


def test_update_unknown_username_returns_404(db, auth_client):
    response = auth_client.patch(update_url("ghost"), {"city": "Nakuru"}, format="json")
    assert response.status_code == 404


def test_update_rejects_invalid_data(db, auth_client, base_user):
    """is_valid() was previously called without raise_exception, so bad input
    was silently accepted."""
    response = auth_client.patch(
        update_url(base_user.username),
        {"phone_number": "not-a-phone-number"},
        format="json",
    )

    assert response.status_code == 400
    base_user.profile.refresh_from_db()
    assert str(base_user.profile.phone_number) != "not-a-phone-number"


def test_update_can_flag_the_user_as_an_agent(db, auth_client, base_user):
    response = auth_client.patch(
        update_url(base_user.username), {"is_agent": True}, format="json"
    )

    assert response.status_code == 200
    base_user.profile.refresh_from_db()
    assert base_user.profile.is_agent is True


def test_update_marks_top_agents_in_the_response(db, auth_client, base_user):
    profile = base_user.profile
    profile.top_agent = True
    profile.save()

    response = auth_client.patch(
        update_url(base_user.username), {"city": "Nairobi"}, format="json"
    )

    assert response.json()["Profile"]["top_agent"] is True


# --------------------------------------------------------------------------
# GET /profile/agents/all/ and /profile/top-agents/all/
# --------------------------------------------------------------------------


def test_agent_list_requires_auth(db, api_client):
    assert api_client.get(AGENTS_URL).status_code == 401


def test_agent_list_returns_only_agents(db, auth_client, user_factory):
    agent_user = user_factory.create()
    agent_user.profile.is_agent = True
    agent_user.profile.save()
    user_factory.create()  # not an agent

    response = auth_client.get(AGENTS_URL)

    usernames = [row["username"] for row in response.data["results"]]
    assert usernames == [agent_user.username]


def test_top_agent_list_requires_auth(db, api_client):
    assert api_client.get(TOP_AGENTS_URL).status_code == 401


def test_top_agent_list_returns_only_top_agents(db, auth_client, user_factory):
    top = user_factory.create()
    top.profile.is_agent = True
    top.profile.top_agent = True
    top.profile.save()

    ordinary = user_factory.create()
    ordinary.profile.is_agent = True
    ordinary.profile.save()

    response = auth_client.get(TOP_AGENTS_URL)

    usernames = [row["username"] for row in response.data["results"]]
    assert usernames == [top.username]


def test_agent_list_is_paginated(db, auth_client, user_factory):
    for _ in range(15):
        user = user_factory.create()
        user.profile.is_agent = True
        user.profile.save()

    response = auth_client.get(AGENTS_URL)

    assert response.data["count"] == 15
    assert len(response.data["results"]) == 12

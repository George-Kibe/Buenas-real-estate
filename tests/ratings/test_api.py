"""API coverage for apps/ratings/urls.py."""

import uuid

from django.urls import reverse

from apps.ratings.models import Rating


def rating_url(profile_id):
    return reverse("create-rating", args=[profile_id])


PAYLOAD = {"rating": 5, "comment": "Answered every question quickly."}


def test_create_review_requires_auth(db, api_client, agent_profile):
    response = api_client.post(rating_url(agent_profile.id), PAYLOAD, format="json")
    assert response.status_code == 401


def test_create_review_returns_201(db, auth_client, agent_profile):
    response = auth_client.post(rating_url(agent_profile.id), PAYLOAD, format="json")

    assert response.status_code == 201
    assert response.data["rating"] == 5
    assert response.data["agent"] == agent_profile.user.username
    assert Rating.objects.count() == 1


def test_create_review_updates_the_agent_aggregate(
    db, auth_client, other_client, agent_profile
):
    auth_client.post(
        rating_url(agent_profile.id), {**PAYLOAD, "rating": 5}, format="json"
    )
    other_client.post(
        rating_url(agent_profile.id), {**PAYLOAD, "rating": 2}, format="json"
    )

    agent_profile.refresh_from_db()
    assert agent_profile.num_reviews == 2
    assert float(agent_profile.rating) == 3.5


def test_you_cannot_review_yourself(db, auth_client, base_user):
    profile = base_user.profile
    profile.is_agent = True
    profile.save()

    response = auth_client.post(rating_url(profile.id), PAYLOAD, format="json")

    assert response.status_code == 403
    assert "rate yourself" in response.data["detail"]


def test_a_second_review_is_rejected(db, auth_client, agent_profile):
    auth_client.post(rating_url(agent_profile.id), PAYLOAD, format="json")

    response = auth_client.post(rating_url(agent_profile.id), PAYLOAD, format="json")

    assert response.status_code == 400
    assert "already reviewed" in response.data["detail"]
    assert Rating.objects.count() == 1


def test_a_different_rater_may_still_review(
    db, auth_client, other_client, agent_profile
):
    auth_client.post(rating_url(agent_profile.id), PAYLOAD, format="json")

    response = other_client.post(rating_url(agent_profile.id), PAYLOAD, format="json")

    assert response.status_code == 201
    assert Rating.objects.count() == 2


def test_unknown_agent_returns_404(db, auth_client):
    response = auth_client.post(rating_url(uuid.uuid4()), PAYLOAD, format="json")
    assert response.status_code == 404


def test_a_non_agent_profile_returns_404(db, auth_client, other_user):
    response = auth_client.post(
        rating_url(other_user.profile.id), PAYLOAD, format="json"
    )
    assert response.status_code == 404


def test_rating_of_zero_is_rejected(db, auth_client, agent_profile):
    response = auth_client.post(
        rating_url(agent_profile.id), {**PAYLOAD, "rating": 0}, format="json"
    )

    assert response.status_code == 400
    assert "rating" in response.data


def test_rating_above_five_is_rejected(db, auth_client, agent_profile):
    response = auth_client.post(
        rating_url(agent_profile.id), {**PAYLOAD, "rating": 9}, format="json"
    )
    assert response.status_code == 400


def test_a_missing_rating_is_rejected(db, auth_client, agent_profile):
    response = auth_client.post(
        rating_url(agent_profile.id), {"comment": "Great"}, format="json"
    )
    assert response.status_code == 400


def test_a_blank_comment_is_rejected(db, auth_client, agent_profile):
    response = auth_client.post(
        rating_url(agent_profile.id), {"rating": 4, "comment": "   "}, format="json"
    )
    assert response.status_code == 400


def test_rating_str(db, rating_factory):
    review = rating_factory.create(rating=4)

    assert str(review) == f"{review.agent} rated at 4"

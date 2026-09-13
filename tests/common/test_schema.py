"""The OpenAPI schema is a shipped artefact (docs/openapi.yaml), so a view that
stops introspecting cleanly should fail the build."""

from drf_spectacular.generators import SchemaGenerator

EXPECTED_PATHS = [
    "/api/v1/auth/jwt/create/",
    "/api/v1/auth/jwt/refresh/",
    "/api/v1/auth/users/",
    "/api/v1/auth/users/me/",
    "/api/v1/enquiries/",
    "/api/v1/profile/agents/all/",
    "/api/v1/profile/me/",
    "/api/v1/profile/top-agents/all/",
    "/api/v1/profile/update/{username}/",
    "/api/v1/properties/agents/",
    "/api/v1/properties/all/",
    "/api/v1/properties/create/",
    "/api/v1/properties/delete/{slug}/",
    "/api/v1/properties/details/{slug}/",
    "/api/v1/properties/search/",
    "/api/v1/properties/update/{slug}/",
    "/api/v1/properties/upload-image/{slug}/",
    "/api/v1/properties/views/",
    "/api/v1/ratings/{profile_id}/",
]


def _schema():
    # Generating the schema instantiates each view with an AnonymousUser, which
    # is what the swagger_fake_view guards in get_queryset() are for.
    return SchemaGenerator().get_schema(request=None, public=True)


def test_every_endpoint_is_documented(db):
    paths = _schema()["paths"]

    missing = [path for path in EXPECTED_PATHS if path not in paths]
    assert missing == [], f"undocumented endpoints: {missing}"


def test_function_based_views_declare_a_request_body(db):
    paths = _schema()["paths"]

    create = paths["/api/v1/properties/create/"]["post"]
    assert "requestBody" in create
    assert "201" in create["responses"]

    review = paths["/api/v1/ratings/{profile_id}/"]["post"]
    assert "requestBody" in review
    assert "403" in review["responses"]


def test_write_serializer_hides_server_owned_fields(db):
    schema = _schema()
    request_schema = schema["components"]["schemas"]["PropertyCreateRequest"]

    for server_owned in ["user", "slug", "ref_code", "views"]:
        assert (
            server_owned not in request_schema["properties"]
        ), f"{server_owned} must not be client-writable"

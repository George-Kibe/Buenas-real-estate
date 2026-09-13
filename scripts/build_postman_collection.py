#!/usr/bin/env python3
"""Generate the Postman collection in docs/ from a single description of the API.

Run with `make postman` (or `python scripts/build_postman_collection.py`) after
adding or changing an endpoint.

The output is Postman Collection v2.1, which Insomnia also imports directly.
"""

import json
import pathlib
import uuid

DOCS = pathlib.Path(__file__).resolve().parent.parent / "docs"

COLLECTION_NAME = "Buenas Real Estate API"
NAMESPACE = uuid.UUID("6f1d7a2e-6d1c-4a8f-9f3a-1c0b2d3e4f50")


def _id(name):
    """Stable ids so regenerating produces a clean diff, not a new collection."""
    return str(uuid.uuid5(NAMESPACE, name))


def test_script(*lines):
    return {
        "listen": "test",
        "script": {"type": "text/javascript", "exec": list(lines)},
    }


def status_test(expected, label=None):
    label = label or f"status is {expected}"
    return test_script(
        f'pm.test("{label}", function () {{',
        f"    pm.response.to.have.status({expected});",
        "});",
    )


def request(
    name,
    method,
    path,
    *,
    body=None,
    query=None,
    auth=True,
    events=None,
    description="",
    form_data=None,
):
    # Django's APPEND_SLASH cannot redirect a POST, so the trailing slash has
    # to survive into Postman's path array — it represents one as a final "".
    segments = [segment for segment in path.strip("/").split("/") if segment]
    if path.endswith("/"):
        segments.append("")

    url = {
        "raw": "{{baseUrl}}" + path,
        "host": ["{{baseUrl}}"],
        "path": segments,
    }
    if query:
        url["query"] = [
            {"key": key, "value": str(value), "disabled": False}
            for key, value in query.items()
        ]
        url["raw"] += "?" + "&".join(f"{k}={v}" for k, v in query.items())

    req = {
        "method": method,
        "header": [],
        "url": url,
        "description": description,
    }

    if form_data is not None:
        req["body"] = {"mode": "formdata", "formdata": form_data}
    elif body is not None:
        req["header"].append(
            {"key": "Content-Type", "value": "application/json", "type": "text"}
        )
        req["body"] = {
            "mode": "raw",
            "raw": json.dumps(body, indent=2),
            "options": {"raw": {"language": "json"}},
        }

    if not auth:
        req["auth"] = {"type": "noauth"}

    item = {"name": name, "_postman_id": _id(name), "request": req}
    if events:
        item["event"] = events
    return item


# --------------------------------------------------------------------------
# Folders
# --------------------------------------------------------------------------

AUTH = [
    request(
        "Register",
        "POST",
        "/api/v1/auth/users/",
        auth=False,
        description=(
            "Creates an **inactive** account and emails an activation link "
            "(DJOSER.SEND_ACTIVATION_EMAIL is on), so this account cannot log "
            "in until it is activated. It uses a throwaway random identity so "
            "it never collides with the seeded login account below.\n\n"
            "For a signed-in session, run `make seed-demo` and use "
            "*Login* with the credentials it prints."
        ),
        body={
            "username": "{{$randomUserName}}",
            "email": "{{$randomEmail}}",
            "first_name": "{{$randomFirstName}}",
            "last_name": "{{$randomLastName}}",
            "password": "{{password}}",
            "re_password": "{{password}}",
        },
        events=[status_test(201, "registration returns 201")],
    ),
    request(
        "Login (obtain JWT pair)",
        "POST",
        "/api/v1/auth/jwt/create/",
        auth=False,
        description=(
            "The login field is the email address, not the username. The "
            "account must be active — run `make seed-demo` to get one.\n\n"
            "Stores `accessToken` and `refreshToken`; every other request "
            "inherits bearer auth from the collection."
        ),
        body={"email": "{{email}}", "password": "{{password}}"},
        events=[
            test_script(
                'pm.test("login returns 200", function () {',
                "    pm.response.to.have.status(200);",
                "});",
                "",
                "const body = pm.response.json();",
                'pm.collectionVariables.set("accessToken", body.access);',
                'if (pm.environment.name) { pm.environment.set("accessToken", body.access); }',
                'pm.collectionVariables.set("refreshToken", body.refresh);',
                'if (pm.environment.name) { pm.environment.set("refreshToken", body.refresh); }',
                "",
                'pm.test("token pair is present", function () {',
                "    pm.expect(body).to.have.property('access');",
                "    pm.expect(body).to.have.property('refresh');",
                "});",
            )
        ],
    ),
    request(
        "Refresh access token",
        "POST",
        "/api/v1/auth/jwt/refresh/",
        auth=False,
        body={"refresh": "{{refreshToken}}"},
        events=[
            test_script(
                'pm.test("refresh returns 200", function () {',
                "    pm.response.to.have.status(200);",
                "});",
                "const access = pm.response.json().access;",
                'pm.collectionVariables.set("accessToken", access);',
                'if (pm.environment.name) { pm.environment.set("accessToken", access); }',
            )
        ],
    ),
    request(
        "Verify access token",
        "POST",
        "/api/v1/auth/jwt/verify/",
        auth=False,
        body={"token": "{{accessToken}}"},
        events=[status_test(200)],
    ),
    request(
        "Current user",
        "GET",
        "/api/v1/auth/users/me/",
        description="Rendered by apps/users/serializers.py::UserSerializer.",
        events=[
            test_script(
                'pm.test("returns the signed-in user", function () {',
                "    pm.response.to.have.status(200);",
                "    pm.expect(pm.response.json().email).to.eql(pm.variables.get('email'));",
                "});",
            )
        ],
    ),
    request(
        "Request a password reset",
        "POST",
        "/api/v1/auth/users/reset_password/",
        auth=False,
        body={"email": "{{email}}"},
        events=[status_test(204)],
    ),
    request(
        "Change password",
        "POST",
        "/api/v1/auth/users/set_password/",
        description=(
            "Changes the account password and updates the `password` variable "
            "so later runs still authenticate."
        ),
        body={
            "current_password": "{{password}}",
            "new_password": "An0therStr0ng!Pass",
            "re_new_password": "An0therStr0ng!Pass",
        },
        events=[
            test_script(
                'pm.test("password change returns 204", function () {',
                "    pm.response.to.have.status(204);",
                "});",
                'pm.collectionVariables.set("password", "An0therStr0ng!Pass");',
                'if (pm.environment.name) { pm.environment.set("password", "An0therStr0ng!Pass"); }',
            )
        ],
    ),
]

PROFILE = [
    request(
        "My profile",
        "GET",
        "/api/v1/profile/me/",
        description=(
            "The body is namespaced under a `Profile` key by "
            "apps/profiles/renderers.py. Error bodies are not wrapped."
        ),
        events=[
            test_script(
                'pm.test("returns a wrapped profile", function () {',
                "    pm.response.to.have.status(200);",
                "    pm.expect(pm.response.json()).to.have.property('Profile');",
                "});",
                "",
                "const profile = pm.response.json().Profile;",
                'pm.collectionVariables.set("profileId", profile.id);',
                'if (pm.environment.name) { pm.environment.set("profileId", profile.id); }',
                "if (profile.is_agent) {",
                '    pm.collectionVariables.set("agentProfileId", profile.id);',
                '    if (pm.environment.name) { pm.environment.set("agentProfileId", profile.id); }',
                "}",
            )
        ],
    ),
    request(
        "Update my profile",
        "PATCH",
        "/api/v1/profile/update/{{username}}/",
        description="You may only update your own profile; anyone else gets a 403.",
        body={
            "about_me": "Agent covering Nairobi and the Rift Valley.",
            "city": "Nakuru",
            "country": "KE",
            "phone_number": "+254712345678",
            "is_agent": True,
            "is_seller": True,
        },
        events=[status_test(200)],
    ),
    request(
        "List agents",
        "GET",
        "/api/v1/profile/agents/all/",
        query={"page": 1, "page_size": 12},
        events=[status_test(200)],
    ),
    request(
        "List top agents",
        "GET",
        "/api/v1/profile/top-agents/all/",
        query={"page": 1},
        events=[status_test(200)],
    ),
]

PROPERTY_BODY = {
    "title": "Lakeside villa in Naivasha",
    "description": "A calm three bedroom home looking over Lake Naivasha.",
    "country": "KE",
    "city": "Naivasha",
    "postal_code": "20117",
    "street_address": "Moi South Lake Road",
    "property_number": 42,
    "price": "12500000.00",
    "tax": "0.15",
    "plot_area": "450.00",
    "total_floors": 2,
    "bedrooms": 3,
    "bathrooms": "2.50",
    "advert_type": "For Sale",
    "property_type": "House",
    "published_status": True,
}

PROPERTIES = [
    request(
        "List properties",
        "GET",
        "/api/v1/properties/all/",
        auth=False,
        description="Public. 12 per page by default.",
        query={"page": 1, "page_size": 12, "ordering": "-created_at"},
        events=[
            test_script(
                'pm.test("returns a paginated envelope", function () {',
                "    pm.response.to.have.status(200);",
                "    pm.expect(pm.response.json()).to.have.property('results');",
                "});",
            )
        ],
    ),
    request(
        "List properties (filtered)",
        "GET",
        "/api/v1/properties/all/",
        auth=False,
        description="advert_type, property_type, price, price__gt, price__lt, search, ordering.",
        query={
            "advert_type": "For Sale",
            "property_type": "House",
            "price__lt": "20000000",
            "search": "Naivasha",
            "ordering": "price",
        },
        events=[status_test(200)],
    ),
    request(
        "Create a property",
        "POST",
        "/api/v1/properties/create/",
        description=(
            "The owner comes from the access token. `user`, `slug`, `ref_code` "
            "and `views` in the body are ignored."
        ),
        body=PROPERTY_BODY,
        events=[
            test_script(
                'pm.test("creation returns 201", function () {',
                "    pm.response.to.have.status(201);",
                "});",
                "",
                "const created = pm.response.json();",
                'pm.collectionVariables.set("propertySlug", created.slug);',
                'if (pm.environment.name) { pm.environment.set("propertySlug", created.slug); }',
                "",
                'pm.test("server owns slug and ref_code", function () {',
                "    pm.expect(created.slug).to.be.a('string').and.not.empty;",
                "    pm.expect(created.ref_code).to.have.lengthOf(10);",
                "    pm.expect(created.views).to.eql(0);",
                "});",
            )
        ],
    ),
    request(
        "Property detail",
        "GET",
        "/api/v1/properties/details/{{propertySlug}}/",
        auth=False,
        description="Public. The first request from a given IP increments `views`.",
        events=[status_test(200)],
    ),
    request(
        "Update a property (PATCH)",
        "PATCH",
        "/api/v1/properties/update/{{propertySlug}}/",
        body={"city": "Nakuru", "price": "13750000.00"},
        events=[status_test(200)],
    ),
    request(
        "Update a property (PUT)",
        "PUT",
        "/api/v1/properties/update/{{propertySlug}}/",
        description="PUT is a full replacement; PATCH is partial.",
        body=PROPERTY_BODY,
        events=[status_test(200)],
    ),
    request(
        "My listings",
        "GET",
        "/api/v1/properties/agents/",
        description="Only the properties owned by the signed-in user.",
        events=[status_test(200)],
    ),
    request(
        "View records for my listings",
        "GET",
        "/api/v1/properties/views/",
        events=[status_test(200)],
    ),
    request(
        "Upload property photos",
        "POST",
        "/api/v1/properties/upload-image/{{propertySlug}}/",
        description=(
            "multipart/form-data. Only the fields you send are replaced — pick "
            "files in Postman's Body tab before sending."
        ),
        form_data=[
            {"key": "cover_photo", "type": "file", "src": [], "disabled": True},
            {"key": "photo1", "type": "file", "src": [], "disabled": True},
            {"key": "photo2", "type": "file", "src": [], "disabled": True},
            {"key": "photo3", "type": "file", "src": [], "disabled": True},
            {"key": "photo4", "type": "file", "src": [], "disabled": True},
        ],
        events=[status_test(200)],
    ),
    request(
        "Search properties",
        "POST",
        "/api/v1/properties/search/",
        auth=False,
        description=(
            "Bracketed values only. price: 0+, 50,000+, 100,000+, 200,000+, "
            "400,000+, 600,000+, Any. bedrooms/bathrooms: 0+ … 5+, Any. "
            "Anything else is a 400."
        ),
        body={
            "advert_type": "For Sale",
            "property_type": "House",
            "price": "Any",
            "bedrooms": "2+",
            "bathrooms": "1+",
            "catch_phrase": "lake",
        },
        events=[status_test(200)],
    ),
    request(
        "Delete a property",
        "DELETE",
        "/api/v1/properties/delete/{{propertySlug}}/",
        description="Run this last — it removes the property the other calls use.",
        events=[status_test(204)],
    ),
]

ENQUIRIES = [
    request(
        "Send an enquiry",
        "POST",
        "/api/v1/enquiries/",
        auth=False,
        description="Public contact form. The email is queued to Celery.",
        body={
            "name": "Ada Smith",
            "email": "ada@example.com",
            "phone_number": "+254712345678",
            "subject": "Viewing request",
            "message": "Could I view the Naivasha villa on Saturday morning?",
        },
        events=[status_test(201)],
    ),
]

RATINGS = [
    request(
        "Review an agent",
        "POST",
        "/api/v1/ratings/{{agentProfileId}}/",
        description=(
            "agentProfileId must be the UUID of a profile with is_agent=true, "
            "and cannot be your own. One review per rater per agent."
        ),
        body={"rating": 5, "comment": "Answered every question quickly."},
        events=[status_test(201)],
    ),
]

SCHEMA = [
    request(
        "OpenAPI schema",
        "GET",
        "/api/v1/schema/",
        auth=False,
        description="Import this URL straight into Postman or Insomnia.",
        events=[status_test(200)],
    ),
    request("Swagger UI", "GET", "/api/v1/docs/", auth=False),
    request("ReDoc", "GET", "/api/v1/redoc/", auth=False),
]

ERRORS = [
    request(
        "401 — no token",
        "GET",
        "/api/v1/profile/me/",
        auth=False,
        description="Every protected route denies by default.",
        events=[status_test(401)],
    ),
    request(
        "404 — unknown property",
        "GET",
        "/api/v1/properties/details/no-such-listing/",
        auth=False,
        events=[status_test(404)],
    ),
    request(
        "400 — invalid search bracket",
        "POST",
        "/api/v1/properties/search/",
        auth=False,
        description="This used to raise a KeyError and return a 500.",
        body={"advert_type": "For Barter"},
        events=[status_test(400)],
    ),
    request(
        "403 — updating someone else's property",
        "PATCH",
        "/api/v1/properties/update/{{someoneElsesSlug}}/",
        description="Set someoneElsesSlug to a listing you do not own.",
        body={"city": "Nakuru"},
        events=[status_test(403)],
    ),
]


def folder(name, items, description=""):
    return {
        "name": name,
        "_postman_id": _id(f"folder:{name}"),
        "description": description,
        "item": items,
    }


COLLECTION = {
    "info": {
        "_postman_id": _id("collection"),
        "name": COLLECTION_NAME,
        "description": (
            "Every endpoint in the Buenas Real Estate API.\n\n"
            "**Getting started**\n"
            "1. Start the stack: `make build`.\n"
            "2. Seed an activated account: `make seed-demo`. It prints the "
            "`email`, `password`, `agentProfileId` and `someoneElsesSlug` to "
            "put in your environment.\n"
            "3. Import `buenas-real-estate.postman_environment.json` and set "
            "`baseUrl` (default http://localhost:8080).\n"
            "4. Hit **Run collection** — *Login* stores the tokens, *Create a "
            "property* stores `propertySlug`, and the detail/update/upload/"
            "delete calls reuse it.\n\n"
            "Every assertion in here is verified against a live server with "
            "`newman run`. The Errors folder asserts the failure paths "
            "(401/403/404/400)."
        ),
        "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
    },
    "auth": {
        "type": "bearer",
        "bearer": [{"key": "token", "value": "{{accessToken}}", "type": "string"}],
    },
    "event": [
        {
            "listen": "prerequest",
            "script": {
                "type": "text/javascript",
                "exec": [
                    "// Default the base URL when neither scope defines one.",
                    "if (!pm.variables.get('baseUrl')) {",
                    "    pm.collectionVariables.set('baseUrl', 'http://localhost:8080');",
                    "}",
                ],
            },
        }
    ],
    "variable": [
        {"key": "baseUrl", "value": "http://localhost:8080", "type": "string"},
        {"key": "username", "value": "asmith", "type": "string"},
        {"key": "email", "value": "asmith@example.com", "type": "string"},
        {"key": "password", "value": "Str0ngPassw0rd!42", "type": "string"},
        {"key": "accessToken", "value": "", "type": "string"},
        {"key": "refreshToken", "value": "", "type": "string"},
        {"key": "propertySlug", "value": "", "type": "string"},
        {"key": "profileId", "value": "", "type": "string"},
        {"key": "agentProfileId", "value": "", "type": "string"},
        {"key": "someoneElsesSlug", "value": "", "type": "string"},
    ],
    "item": [
        folder("Auth", AUTH, "Registration, JWT and account management (djoser)."),
        folder("Profile", PROFILE, "The profile attached to each user."),
        folder("Properties", PROPERTIES, "Listings: browse, create, update, delete."),
        folder("Enquiries", ENQUIRIES, "Public contact form."),
        folder("Ratings", RATINGS, "Agent reviews."),
        folder("Schema", SCHEMA, "OpenAPI schema and rendered docs."),
        folder("Errors", ERRORS, "Expected failure paths, asserted."),
    ],
}

ENVIRONMENT = {
    "id": _id("environment:local"),
    "name": "Buenas Real Estate — Local",
    "values": [
        {"key": "baseUrl", "value": "http://localhost:8080", "enabled": True},
        {"key": "username", "value": "asmith", "enabled": True},
        {"key": "email", "value": "asmith@example.com", "enabled": True},
        {"key": "password", "value": "Str0ngPassw0rd!42", "enabled": True},
        {"key": "accessToken", "value": "", "enabled": True},
        {"key": "refreshToken", "value": "", "enabled": True},
        {"key": "propertySlug", "value": "", "enabled": True},
        {"key": "profileId", "value": "", "enabled": True},
        {"key": "agentProfileId", "value": "", "enabled": True},
        {"key": "someoneElsesSlug", "value": "", "enabled": True},
    ],
    "_postman_variable_scope": "environment",
}


def main():
    DOCS.mkdir(parents=True, exist_ok=True)

    collection_path = DOCS / "buenas-real-estate.postman_collection.json"
    environment_path = DOCS / "buenas-real-estate.postman_environment.json"

    collection_path.write_text(json.dumps(COLLECTION, indent=2) + "\n")
    environment_path.write_text(json.dumps(ENVIRONMENT, indent=2) + "\n")

    count = sum(len(f["item"]) for f in COLLECTION["item"])
    print(f"Wrote {collection_path} ({count} requests)")
    print(f"Wrote {environment_path}")


if __name__ == "__main__":
    main()

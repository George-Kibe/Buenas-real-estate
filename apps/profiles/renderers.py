from rest_framework.renderers import JSONRenderer


class ProfileJSONRenderer(JSONRenderer):
    """Namespaces successful profile payloads under a "Profile" key.

    Error bodies are passed through untouched: wrapping a 403 or a validation
    error in "Profile" makes it unreadable to clients, which look for `detail`.
    """

    charset = "utf-8"

    def render(self, data, accepted_media_type=None, renderer_context=None):
        response = (renderer_context or {}).get("response")
        is_error = response is not None and response.status_code >= 400

        if is_error or not isinstance(data, dict):
            return super().render(data, accepted_media_type, renderer_context)

        return super().render({"Profile": data}, accepted_media_type, renderer_context)

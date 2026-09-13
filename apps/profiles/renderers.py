import json

from rest_framework.renderers import JSONRenderer


class ProfileJSONRenderer(JSONRenderer):
    charset = "utf-8"

    def render(self, data, accepted_media_type=None, renderer_context=None):
        errors = data.get("errors", None) if isinstance(data, dict) else None

        if errors is not None:
            return super().render(data, accepted_media_type, renderer_context)
        return json.dumps({"Profile": data})

from rest_framework import serializers

from .models import Rating


class RatingSerializer(serializers.ModelSerializer):
    rater = serializers.CharField(source="rater.username", read_only=True)
    agent = serializers.CharField(source="agent.user.username", read_only=True)

    class Meta:
        model = Rating
        fields = ["id", "rater", "agent", "rating", "comment", "created_at"]
        read_only_fields = fields


class CreateRatingSerializer(serializers.ModelSerializer):
    """Write representation. `rater` and `agent` come from the URL and the
    token, never the body."""

    # The model field carries default=0, which would make it optional here.
    rating = serializers.IntegerField(required=True)

    class Meta:
        model = Rating
        fields = ["rating", "comment"]

    def validate_rating(self, value):
        if value not in dict(Rating.Range.choices):
            raise serializers.ValidationError(
                "Rating must be a whole number between 1 and 5."
            )
        return value

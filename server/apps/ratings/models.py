from enum import unique
from django.db import models
from django.utils.translation import gettext_lazy as _
from buenas_real_estate.settings.base import AUTH_USER_MODEL
from apps.common.models import TimeStampedUUIDModel
from apps.profiles.models import Profile

# Create your models here.
class Rating(TimeStampedUUIDModel):
    class Range(models.IntegerChoices):
        RATING_1 = 1, _("Poor")
        RATING_2 = 2, _("Fair")
        RATING_3 = 3, _("Good")
        RATING_4 = 4, _("Very Good")
        RATING_5 = 5, _("Excellent")

    rater = models.ForeignKey(AUTH_USER_MODEL, verbose_name=_("Client Rating Agent"), on_delete=models.SET_NULL, null=True)
    agent = models.ForeignKey(Profile, verbose_name=_("Agent Getting reviewed"), on_delete=models.SET_NULL, null=True, related_name="agent_review")
    rating = models.IntegerField(verbose_name=_("Rating"), choices=Range.choices, help_text="1=Poor, 2=Fair, 3=Good, 4=Very Good, 5=Excellent", default=0)
    comment = models.TextField(verbose_name=_("Comment"))

    class Meta:
        unique_together = ["rater", "agent"]
    def __str__(self):
        return f"{self.agent} rated at {self.rating}"





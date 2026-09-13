import logging

from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.profiles.models import Profile

logger = logging.getLogger(__name__)


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
        logger.info("Created a profile for %s", instance)


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def save_user_profile(sender, instance, **kwargs):
    # A user created outside the signal (fixtures, data migrations) may not
    # have a profile yet; get_or_create keeps this idempotent.
    profile, _created = Profile.objects.get_or_create(user=instance)
    profile.save()

from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django_countries.fields import CountryField
from phonenumber_field.modelfields import PhoneNumberField
from apps.common.models import TimeStampedUUIDModel

User = get_user_model()
# Create your models here.
class Gender(models.TextChoices):
    MALE = "Male", _("Male")
    FEMALE = "Female", _("Female")
    OTHER = "Other", _("Other")

class Profile(TimeStampedUUIDModel):
    user = models.OneToOneField(User, related_name="profile", on_delete=models.CASCADE)
    phone_number = PhoneNumberField(verbose_name=_("Phone Number"), default="+254712345678", max_length=25)
    about_me = models.TextField(verbose_name=_("About Me"), default="Say something about yourself", max_length=255)
    license_info = models.CharField(verbose_name=_("Real Estate License"), blank=True, null=True, max_length=255)
    profile_photo = models.ImageField(verbose_name=_("Profile Photo"), default="/profile_default.png", max_length=255)
    gender = models.CharField(verbose_name=_("Gender"), choices=Gender.choices, default=Gender.OTHER, max_length=255)
    country = CountryField(verbose_name=_("Country"), default="Kenya", blank=True, null=True, max_length=255)
    city = models.CharField(verbose_name=_("City"), default="Nairobi", blank=True, null=True, max_length=255)
    is_buyer = models.BooleanField(verbose_name=_("Buyer"), default=False, help_text=_("Are you looking for a property"))
    is_seller = models.BooleanField(verbose_name=_("Seller"), default=False, help_text=_("Are you selling a property"))
    is_agent = models.BooleanField(verbose_name=_("Agent"), default=False, help_text=_("Are you an Agent"))
    top_agent = models.BooleanField(verbose_name=_("Top Agent"), default=False, help_text=_("Are you a Top Agent"))
    rating = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    num_reviews = models.IntegerField(verbose_name=_("Reviews"), default=0, null=True, blank=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"































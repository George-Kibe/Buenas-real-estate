import factory
from django.conf import settings
from django.db.models.signals import post_save
from faker import Factory as FakerFactory

from apps.enquiries.models import Enquiry
from apps.profiles.models import Profile
from apps.properties.models import Property
from apps.ratings.models import Rating

faker = FakerFactory.create()


@factory.django.mute_signals(post_save)
class ProfileFactory(factory.django.DjangoModelFactory):
    user = factory.SubFactory("tests.factories.UserFactory")
    phone_number = "+254712345678"
    about_me = factory.LazyAttribute(lambda x: faker.sentence(nb_words=5))
    license_info = factory.LazyAttribute(lambda x: faker.text(max_nb_chars=6))
    profile_photo = "/profile_default.png"
    gender = "Other"
    country = "KE"
    city = factory.LazyAttribute(lambda x: faker.city())
    is_buyer = False
    is_seller = False
    is_agent = False
    top_agent = False
    rating = factory.LazyAttribute(lambda x: faker.random_int(min=1, max=5))
    num_reviews = factory.LazyAttribute(lambda x: faker.random_int(min=0, max=25))

    class Meta:
        model = Profile


class UserFactory(factory.django.DjangoModelFactory):
    """Signals stay live here so every user gets its Profile, the way the app
    creates them."""

    first_name = factory.LazyAttribute(lambda x: faker.first_name())
    last_name = factory.LazyAttribute(lambda x: faker.last_name())
    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.Sequence(lambda n: f"user{n}@example.com")
    password = factory.LazyAttribute(lambda x: faker.password())
    is_active = True
    is_staff = False

    class Meta:
        model = settings.AUTH_USER_MODEL
        skip_postgeneration_save = True

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        manager = cls._get_manager(model_class)
        # Passing is_superuser at all routes through create_superuser, so its
        # validation rules can be exercised with either value.
        if "is_superuser" in kwargs:
            return manager.create_superuser(*args, **kwargs)
        return manager.create_user(*args, **kwargs)


class PropertyFactory(factory.django.DjangoModelFactory):
    user = factory.SubFactory(UserFactory)
    title = factory.Sequence(lambda n: f"Property Number {n}")
    description = factory.LazyAttribute(lambda x: faker.paragraph(nb_sentences=2))
    country = "KE"
    city = factory.LazyAttribute(lambda x: faker.city())
    postal_code = "140"
    street_address = "Moi Avenue"
    property_number = 112
    price = factory.LazyAttribute(
        lambda x: faker.pydecimal(left_digits=7, right_digits=2, positive=True)
    )
    tax = "0.15"
    plot_area = "450.00"
    total_floors = 2
    bedrooms = 3
    bathrooms = "2.50"
    advert_type = Property.AdvertType.FOR_SALE
    property_type = Property.PropertyType.HOUSE
    published_status = True

    class Meta:
        model = Property


def _agent_profile():
    """Every user already has a Profile from the post_save signal, so reuse it
    rather than creating a second one through ProfileFactory."""
    user = UserFactory.create()
    profile = user.profile
    profile.is_agent = True
    profile.save()
    return profile


class RatingFactory(factory.django.DjangoModelFactory):
    rater = factory.SubFactory(UserFactory)
    agent = factory.LazyFunction(_agent_profile)
    rating = 4
    comment = factory.LazyAttribute(lambda x: faker.sentence(nb_words=8))

    class Meta:
        model = Rating


class EnquiryFactory(factory.django.DjangoModelFactory):
    name = factory.LazyAttribute(lambda x: faker.name())
    phone_number = "+254712345678"
    email = factory.Sequence(lambda n: f"enquiry{n}@example.com")
    subject = factory.LazyAttribute(lambda x: faker.sentence(nb_words=4))
    message = factory.LazyAttribute(lambda x: faker.paragraph(nb_sentences=2))

    class Meta:
        model = Enquiry

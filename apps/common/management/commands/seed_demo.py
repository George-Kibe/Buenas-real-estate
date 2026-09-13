"""Create the activated accounts and sample data the API collection expects.

djoser creates accounts inactive and emails an activation link, which an API
client cannot follow. This command provides a ready-to-use account so
`docs/buenas-real-estate.postman_collection.json` runs end to end.

Development use only — it sets a known password.
"""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.properties.models import Property

User = get_user_model()

DEMO_PASSWORD = "Str0ngPassw0rd!42"


class Command(BaseCommand):
    help = "Seed an activated demo user, an agent and a sample listing."

    def add_arguments(self, parser):
        parser.add_argument(
            "--password",
            default=DEMO_PASSWORD,
            help="Password for both demo accounts.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        from django.conf import settings

        if not settings.DEBUG:
            raise CommandError("seed_demo refuses to run with DEBUG off.")

        password = options["password"]

        demo = self._upsert_user(
            username="asmith",
            email="asmith@example.com",
            first_name="Ada",
            last_name="Smith",
            password=password,
        )

        agent = self._upsert_user(
            username="bagent",
            email="agent@example.com",
            first_name="Ben",
            last_name="Agent",
            password=password,
        )
        agent_profile = agent.profile
        agent_profile.is_agent = True
        agent_profile.top_agent = True
        agent_profile.about_me = "Sells lakeside property around Naivasha."
        agent_profile.save()

        listing, _ = Property.objects.get_or_create(
            user=agent,
            title="Agent Owned Show House",
            defaults={
                "description": "A sample listing owned by the agent account.",
                "city": "Naivasha",
                "price": "8500000.00",
                "bedrooms": 4,
                "published_status": True,
            },
        )

        self.stdout.write(self.style.SUCCESS("Demo data ready.\n"))
        self.stdout.write("Set these in your Postman/Insomnia environment:\n")
        self.stdout.write(f"  email             = {demo.email}")
        self.stdout.write(f"  username          = {demo.username}")
        self.stdout.write(f"  password          = {password}")
        self.stdout.write(f"  agentProfileId    = {agent_profile.id}")
        self.stdout.write(f"  someoneElsesSlug  = {listing.slug}")

    def _upsert_user(self, *, username, email, first_name, last_name, password):
        user = User.objects.filter(email=email).first()
        if user is None:
            user = User.objects.create_user(
                username=username,
                email=email,
                first_name=first_name,
                last_name=last_name,
                password=password,
            )
        else:
            user.set_password(password)

        # djoser leaves new accounts inactive until the emailed link is used.
        user.is_active = True
        user.save()
        return user

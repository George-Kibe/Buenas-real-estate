import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "real_estate.settings.development")

app = Celery("real_estate")

# Read every CELERY_* key from the active Django settings module.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Discover tasks.py in each installed app.
app.autodiscover_tasks()

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'buenas_real_estate.settings.development')

application = get_wsgi_application()

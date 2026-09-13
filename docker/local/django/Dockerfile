# Django 6.1 requires Python 3.12+.
FROM python:3.14-slim-trixie

LABEL maintainer="georgekibew@gmail.com"
LABEL website="https://www.comparables.co.ke"
LABEL description="Development image for the Buenas Real Estate API"

ENV APP_HOME=/app \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR $APP_HOME
RUN mkdir -p $APP_HOME/staticfiles $APP_HOME/mediafiles $APP_HOME/logs

# psycopg[binary] ships its own libpq, so no build toolchain or libpq-dev here.
RUN apt-get update \
  && apt-get install -y --no-install-recommends gettext \
  && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
  && rm -rf /var/lib/apt/lists/*

COPY ./requirements.txt ./requirements-dev.txt $APP_HOME/
RUN pip install -r requirements-dev.txt

COPY ./docker/local/django/entrypoint /entrypoint
COPY ./docker/local/django/start /start
COPY ./docker/local/django/celery/worker/start /start-celeryworker
COPY ./docker/local/django/celery/flower/start /start-flower
RUN sed -i 's/\r$//g' /entrypoint /start /start-celeryworker /start-flower \
  && chmod +x /entrypoint /start /start-celeryworker /start-flower

ENTRYPOINT ["/entrypoint"]

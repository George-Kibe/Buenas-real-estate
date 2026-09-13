ifneq (,$(wildcard ./.env))
include .env
export
ENV_FILE_PARAM = --env-file .env
endif

.PHONY: build up down show-logs migrate makemigrations superuser collectstatic \
        down-v volume estate-db test test-html flake8 black-check black-diff black \
        isort-check isort-diff isort lint client-install client-lint client-build shell

# --- Stack ---
build:
	docker compose up --build -d --remove-orphans

up:
	docker compose up -d

down:
	docker compose down

down-v:
	docker compose down -v

show-logs:
	docker compose logs -f

# --- Django ---
migrate:
	docker compose exec api python manage.py migrate

makemigrations:
	docker compose exec api python manage.py makemigrations

superuser:
	docker compose exec api python manage.py createsuperuser

collectstatic:
	docker compose exec api python manage.py collectstatic --no-input --clear

shell:
	docker compose exec api python manage.py shell

# --- Database ---
volume:
	docker volume inspect buenas-real-estate_postgres_data

estate-db:
	docker compose exec postgres-db psql --username=$(POSTGRES_USER) --dbname=$(POSTGRES_DB)

# --- Backend quality ---
test:
	docker compose exec api pytest -p no:warnings --cov=.

test-html:
	docker compose exec api pytest -p no:warnings --cov=. --cov-report html

flake8:
	docker compose exec api flake8 .

black-check:
	docker compose exec api black --check .

black-diff:
	docker compose exec api black --diff .

black:
	docker compose exec api black .

isort-check:
	docker compose exec api isort . --check-only

isort-diff:
	docker compose exec api isort . --diff

isort:
	docker compose exec api isort .

lint: flake8 black-check isort-check

# --- Frontend ---
client-install:
	docker compose exec client npm install

client-lint:
	docker compose exec client npm run lint

client-build:
	docker compose exec client npm run build

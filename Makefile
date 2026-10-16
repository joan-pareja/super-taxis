# These targets are commands, not files; always run them when requested.
.PHONY: start-app stop-app upgrade-db downgrade-db

ifeq ($(strip $(MAKECMDGOALS)),)
$(error Specify a target: start-app, stop-app, upgrade-db or downgrade-db)
endif

start-app:
	docker compose up --build -d app

stop-app:
	docker compose down

upgrade-db:
	docker compose run --build --rm app alembic upgrade head

downgrade-db:
	docker compose run --build --rm app alembic downgrade -1

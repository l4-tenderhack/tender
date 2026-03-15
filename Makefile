run:
	docker compose -f docker-compose.yml -f docker-compose.ml.yml up --build app

test:
	docker compose -f docker-compose.yml -f docker-compose.ml.yml run --rm app pytest

lint:
	docker compose -f docker-compose.yml -f docker-compose.ml.yml run --rm app ruff check .

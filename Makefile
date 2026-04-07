up:
	docker-compose up -d

down:
	docker-compose down

rebuild:
	docker-compose build --no-cache --force-rm

build:
	docker-compose build

init:
	docker-compose up -d --build

backend:
	docker-compose exec backend /bin/bash

lint:
	uv run ruff check --fix . && uv run ruff format .

lint-check:
	uv run ruff check . && uv run ruff format --check .

typecheck:
	uv run pyright

test:
	uv run pytest

test-cov:
	uv run pytest --cov=src --cov-report=term-missing

dead:
	uv run vulture src

deps:
	uv run deptry src

security:
	uv run pip-audit

ci: lint-check typecheck test dead deps security

devui:
	uv run python -m src.playground.devui

# --- Playground ---
# make playground m=<module>      — MockChatClient で実行 (課金ゼロ)
# make playground-llm m=<module>  — 本物の LLM で実行 (課金あり)
playground:
	uv run python -m src.playground $(m)

playground-llm:
	ALLOW_LLM_CALLS=true uv run python -m src.playground $(m)

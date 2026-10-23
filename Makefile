.PHONY: setup dev test lint eval eval-fast types docker docker-local e2e

UV ?= uv
PNPM ?= pnpm
export PATH := $(HOME)/.local/bin:$(PATH)

setup:
	cd backend && $(UV) sync --all-extras
	cd frontend && $(PNPM) install
	$(MAKE) types || true

dev:
	@echo "API :8000  |  Web :3000"
	cd backend && $(UV) run uvicorn app.main:app --reload --port 8000 &
	cd frontend && $(PNPM) dev

test:
	cd backend && $(UV) run pytest -q --cov=app --cov-report=term-missing
	cd frontend && $(PNPM) test

lint:
	cd backend && $(UV) run ruff check app tests
	cd frontend && $(PNPM) exec tsc --noEmit

# Internal CI quality harness (not a public route)
eval:
	cd backend && $(UV) run python tests/quality/run_eval.py

eval-fast:
	cd backend && $(UV) run python tests/quality/run_eval.py --fast

types:
	cd backend && $(UV) run python -c "from app.main import app; import json; print('openapi ok', len(app.openapi()['paths']) if app.openapi_url else 0)"
	@echo "Write OpenAPI → frontend/src/types/api.d.ts (openapi-typescript) when ready"

docker:
	docker compose --profile default up --build

docker-local:
	docker compose --profile local up --build

e2e:
	cd frontend && $(PNPM) exec playwright test || echo "Playwright optional — install browsers first"

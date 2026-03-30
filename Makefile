# Flussonic Exporter — dev / test / build
# Usage: make help

PYTHON      ?= python3
PIP         ?= pip3
IMAGE       ?= flussonic-exporter:local
COMPOSE     ?= docker compose

.PHONY: help install install-dev test test-verbose lint format fix check ci clean \
	pre-commit-install pre-commit-run build docker-run compose-up compose-down compose-monitoring run

help:
	@echo "Flussonic Exporter — common targets"
	@echo ""
	@echo "  make install          Install runtime deps (requirements.txt)"
	@echo "  make install-dev      Install runtime + dev deps (requirements-dev.txt)"
	@echo "  make test             Run pytest (quiet)"
	@echo "  make test-verbose     Run pytest with -v --tb=short"
	@echo "  make lint             ruff check + black --check + mypy (no writes)"
	@echo "  make format           black + ruff check --fix (format & auto-fix)"
	@echo "  make fix              ruff check --fix only"
	@echo "  make check            Alias for lint"
	@echo "  make ci               lint + test (same idea as GitHub Actions)"
	@echo "  make clean            Remove caches (__pycache__, .pytest_cache, .mypy_cache, .ruff_cache)"
	@echo "  make pre-commit-install   pip install pre-commit && pre-commit install"
	@echo "  make pre-commit-run       Run all pre-commit hooks on repo"
	@echo "  make build            docker build -t $(IMAGE)"
	@echo "  make docker-run       docker run exporter (export FLUSSONIC_IP/USER/PASSWORD first)"
	@echo "  make compose-up       docker compose up -d (exporter only)"
	@echo "  make compose-down     docker compose down"
	@echo "  make compose-monitoring  docker compose --profile monitoring up -d"
	@echo "  make run              Run exporter locally: $(PYTHON) -m flussonic_exporter"
	@echo ""
	@echo "Variables: PYTHON=$(PYTHON) IMAGE=$(IMAGE)"

install:
	$(PIP) install -r requirements.txt

install-dev:
	$(PIP) install -r requirements.txt -r requirements-dev.txt

test:
	$(PYTHON) -m pytest tests/ -q

test-verbose:
	$(PYTHON) -m pytest tests/ -v --tb=short

lint:
	$(PYTHON) -m ruff check flussonic_exporter tests
	$(PYTHON) -m black --check flussonic_exporter tests
	$(PYTHON) -m mypy flussonic_exporter

format:
	$(PYTHON) -m black flussonic_exporter tests
	$(PYTHON) -m ruff check flussonic_exporter tests --fix

fix:
	$(PYTHON) -m ruff check flussonic_exporter tests --fix

check: lint

ci: lint test

clean:
	rm -rf .pytest_cache .mypy_cache .ruff_cache
	find . -type d -name '__pycache__' -delete 2>/dev/null || true

pre-commit-install:
	$(PIP) install pre-commit
	pre-commit install

pre-commit-run:
	pre-commit run --all-files

build:
	docker build -t $(IMAGE) .

docker-run: build
	docker run --rm -p 9105:9105 \
		-e FLUSSONIC_IP \
		-e FLUSSONIC_USERNAME \
		-e FLUSSONIC_PASSWORD \
		-e FLUSSONIC_PORT \
		-e FLUSSONIC_SERVER_ID \
		-e FLUSSONIC_SCHEME \
		-e FLUSSONIC_HTTPS \
		$(IMAGE)

compose-up:
	$(COMPOSE) up -d

compose-down:
	$(COMPOSE) down

compose-monitoring:
	$(COMPOSE) --profile monitoring up -d

run:
	$(PYTHON) -m flussonic_exporter

# Makefile for hc_p1me

.DEFAULT_GOAL := help
.PHONY: build up down restart rebuild logs logs-tail ps stop start shell health run dev install clean help

# ---------------------------------------------------------
# Python interpreter (venv preferred, fallback python3)
# ---------------------------------------------------------
CONTAINER := $(shell basename $(CURDIR))
PYTHON := $(shell if [ -f /dockerapps/apps_v2/.venv/bin/python ]; then echo /dockerapps/apps_v2/.venv/bin/python; else echo python3; fi)

# ---------------------------------------------------------
# Lokales Ausfuehren
# ---------------------------------------------------------
run: ## Startet lokal mit uvicorn
	@$(PYTHON) -m uvicorn app.main:app --host 0.0.0.0 --port 8096 --no-access-log --log-level warning

dev: ## Startet lokal mit auto-reload
	@$(PYTHON) -m uvicorn app.main:app --host 0.0.0.0 --port 8096 --reload --no-access-log --log-level warning

# ---------------------------------------------------------
# Docker
# ---------------------------------------------------------
build: ## Build Docker image
	docker compose build

up: ## Start containers
	docker compose up -d

down: ## Stop containers
	docker compose down

restart: ## Restart containers
	docker compose restart

rebuild: ## Rebuild and restart (no cache)
	docker compose down
	docker compose build --no-cache
	docker compose up -d --force-recreate

logs: ## Show logs (follow)
	docker compose logs -f

logs-tail: ## Last 100 log lines
	docker compose logs --tail=100

ps: ## Running containers
	docker compose ps

stop: ## Stop containers
	docker compose stop

start: ## Start stopped containers
	docker compose start

shell: ## Shell into container
	docker compose exec $(CONTAINER) /bin/bash

health: ## Check health endpoint
	@curl -sf http://localhost:5045/api/satus | python3 -m json.tool || echo "UNHEALTHY"

# ---------------------------------------------------------
# Development
# ---------------------------------------------------------
install: ## Install dependencies
	@pip install -r requirements.txt

clean: ## Remove cache files
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -name "*.pyc" -delete 2>/dev/null || true

reset: ## Reset DB vom Server holen und App starten (dev)
	@echo "🗑️  Lösche alte Datenbank und State..."
	@rm -f data/sensors_2026.db data/sensor_state.json
	@echo "📥 Hole neue Datenbank vom Server..."
	@scripts/import_from_server.sh 2026
	@echo "📋 Kopiere nach data/..."
	@cp scripts/data/sensors_2026.db data/sensors_2026.db
	@echo "🚀 Starte App..."
	@$(PYTHON) -m uvicorn app.main:app --host 0.0.0.0 --port 8096 --reload --no-access-log --log-level warning


status-app: ## Check if app is running
	@if lsof -ti:5045 >/dev/null 2>&1; then \
		echo "✓ App is running on port 5045 (PID: $$(lsof -ti:5045))"; \
	else \
		echo "✗ App not running"; \
		echo "  Start: make tasmota / make p1meter / make both / make dev"; \
	fi

validate: ## python testcases laufen lassen
	pytest -v

test-config: ## Test app_config.py (neue Struktur)
	pytest -v tests/v3/test_app_config.py

test-config-verbose: ## Test app_config.py mit Details
	pytest -vv tests/v3/test_app_config.py -s

test-v3: ## Alle v3 Tests
	pytest -v tests/v3/

graph: ## Klassen und Ablauf diagram
	PYTHONPATH=. pyreverse -o png -p Smartmeterdata app

git-update: ## Git Forgejo Update durchführen
	git remote set-url origin http://10.1.1.119:3043/peter/hc_scale.git
	git add -A
	git commit -m "Update am $$(date +'%Y-%m-%d %H:%M')" || true
	git push -u origin main

# ---------------------------------------------------------
# Help
# ---------------------------------------------------------
help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

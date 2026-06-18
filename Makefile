# Makefile for hc-smet

# --- 1. DYNAMISCHE PARAMETER & VARIABLEN ---
PROJECT_NAME = $(notdir $(CURDIR))
FORGEJO_IP   = 10.1.1.19
FORGEJO_PORT = 3143
FORGEJO_USER = peter
FORGEJO_URL  = http://$(FORGEJO_IP):$(FORGEJO_PORT)/$(FORGEJO_USER)/$(PROJECT_NAME).git

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

jsbuild: ## 🔧 Komprimiert JS und CSS parallel über Docker – maximal optimiert
	@echo "📦 Starte JS & CSS Bundling via Docker & esbuild..."
	@cp ../shared/themes/theme.css frontend/static/css/theme.css
	@docker run --rm -v "$$(pwd)":/app -w /app node:20-alpine sh -c "\
		npx esbuild frontend/static/js/main.js --bundle --minify --sourcemap --target=es2020 --outfile=frontend/static/js/app.bundle.js && \
		npx esbuild frontend/static/js/live/main.js --bundle --minify --sourcemap --target=es2020 --outfile=frontend/static/js/live/main.bundle.js && \
		npx esbuild frontend/static/css/style.css --bundle --minify --sourcemap --outfile=frontend/static/css/style.bundle.css && \
		npx esbuild frontend/static/css/live.css --minify --sourcemap --outfile=frontend/static/css/live.bundle.css"
	@echo "✅ Fertig!"

jsclean: ## 🔧 Komprimiert JS und CSS entfernen
	@echo "🧼 Bereinige produktive Build-Dateien..."
	@rm -f frontend/static/js/app.bundle.js
	@rm -f frontend/static/js/app.bundle.js.map
	@rm -f frontend/static/css/style.bundle.css
	@rm -f frontend/static/css/style.bundle.css.map
	@echo "✨ Verzeichnis ist wieder sauber."

git-status: ## Zeigt die aktuelle Forgejo Server-Verbindung (Remote URL) an
	@echo "🔍 Überprüfe Git-Remote-Konfiguration..."
	@if ! git remote get-url origin >/dev/null 2>&1; then \
		echo "❌ Fehler: 'origin' ist noch nicht eingerichtet!"; \
		echo "👉 Bitte führe aus: make git-setup"; \
		exit 1; \
	fi
	@URL=$$(git remote get-url origin); \
	echo "🍏 Forgejo-Server ist aktiv verbunden!" ; \
	echo "🔗 Aktuelle URL: $$URL"

git-setup: ## Git-Verbindung zum Forgejo-Server automatisch einrichten oder korrigieren
	@echo "🛠️ Initialisiere Forgejo Server-Verbindung für '$(PROJECT_NAME)'..."
	@if ! git remote get-url origin >/dev/null 2>&1; then \
		git remote add origin $(FORGEJO_URL); \
		echo "🎉 Server-URL erfolgreich neu angelegt!"; \
	else \
		git remote set-url origin $(FORGEJO_URL); \
		echo "🔄 Bestehende Server-URL erfolgreich korrigiert!"; \
	fi
	@echo "🔗 Ziel-Adresse: $(FORGEJO_URL)"

git-update: git-status ## Git Forgejo Update durchführen (Normaler Zwischenstand)
	git add -A
	git commit -m "Update am $$(date +'%Y-%m-%d %H:%M')" || true
	git push -u origin main

git-release: git-status ## Neues Versions-Tag automatisch berechnen, erstellen und zu Forgejo pushen
	git add -A
	git commit -m "Release-Vorbereitung am $$(date +'%Y-%m-%d %H:%M')" || true
	git push origin main
	@LAST_TAG=$$(git describe --tags --abbrev=0 2>/dev/null || echo "v2.1.0"); \
	NEXT_TAG=$$(echo $$LAST_TAG | awk -F. '{print $$1"."$$2"."$$3+1}'); \
	echo "🍏 Letzte Version war: $$LAST_TAG"; \
	echo "⚡ Berechnete neue Version: $$NEXT_TAG"; \
	echo "📦 Erstelle Git-Tag $$NEXT_TAG mit aktuellem Zeitstempel..."; \
	git tag -a $$NEXT_TAG -m "Automatisches Release $$NEXT_TAG am $$(date +'%Y-%m-%d %H:%M') via Makefile"; \
	git push origin $$NEXT_TAG; \
	echo "🎉 Version $$NEXT_TAG erfolgreich an Forgejo übermittelt!"


# ---------------------------------------------------------
# Help
# ---------------------------------------------------------
help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

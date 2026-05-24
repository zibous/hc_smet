.DEFAULT_GOAL := help
.PHONY: build up down restart rebuild logs logs-tail ps stop start shell health run dev install clean help

# ---------------------------------------------------------
# Dynamic Environment & Variables
# ---------------------------------------------------------
CONTAINER := $(shell basename $(CURDIR))
PYTHON := $(shell if [ -f /dockerapps/apps_v2/.venv/bin/python ]; then echo /dockerapps/apps_v2/.venv/bin/python; else echo python3; fi)

# ✨ ZENTRALE VARIABLEN FÜR DEINE STRUKTUR
DB_DIR := ../data
LOG_FILE := $(DB_DIR)/analytics.log
SQLITE_DB := $(DB_DIR)/analytics.sqlite

# ---------------------------------------------------------
# ℹ️ HELP SYSTEM
# ---------------------------------------------------------
help:
	@echo "======================================================================="
	@echo "⚡ LABELS FOR APP: $(CONTAINER)"
	@echo "======================================================================="
	@echo "LOKALER TEST-MODUS (Nutzt: $(PYTHON)):"
	@echo "  make install    - Installiert Abhängigkeiten aus requirements.txt"
	@echo "  make run        - Führt die Pipeline einmalig lokal aus"
	@echo "  make db-check   - Zeigt Inhalt der lokalen analytics.sqlite"
	@echo "  make log-local  - Zeigt die lokalen analytics.log Einträge"
	@echo ""
	@echo "DOCKER CONTAINER MANAGEMENT:"
	@echo "  make build      - Baut das Docker Image"
	@echo "  make up         - Startet den Analytics-Daemon im Hintergrund (-d)"
	@echo "  make down       - Stoppt und entfernt den Container"
	@echo "  make restart    - Startet den Container neu"
	@echo "  make rebuild    - Baut das Image neu und startet den Container"
	@echo "  make logs       - Zeigt alle Container-Logs an"
	@echo "  make logs-tail  - Folgt den Container-Logs live (-f)"
	@echo "  make ps         - Zeigt den Status des Containers an"
	@echo "  make shell      - Öffnet eine interaktive Shell im Container"
	@echo "  make clean      - Bereinigt Cache-Dateien und lokale Testdaten"

# ---------------------------------------------------------
# 🐍 LOKALE ENTWICKLUNG & TESTING
# ---------------------------------------------------------
install:
	@echo "📥 Installiere Abhängigkeiten aus requirements.txt via $(PYTHON)..."
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -r requirements.txt

run:
	@echo "🚀 Starte lokalen Testlauf (Einmalige Pipeline-Ausführung)..."
	PYTHONPATH=. $(PYTHON) -c "import analytics; analytics.run_pipeline()"

log-local:
	@echo "📝 Letzte Einträge aus $(LOG_FILE):"
	@if [ -f $(LOG_FILE) ]; then tail -n 20 $(LOG_FILE); else echo "⚠️ Keine Logdatei vorhanden."; fi

db-check:
	@echo "📊 Inhalt der generierten $(SQLITE_DB):"
	@if [ -f $(SQLITE_DB) ]; then \
		echo "\n--- Jahresbericht ---"; \
		sqlite3 $(SQLITE_DB) "SELECT * FROM yearly_report;"; \
		echo "\n--- Top 5 Monats/Jahreswerte ---"; \
		sqlite3 $(SQLITE_DB) "SELECT * FROM sensor_monthly LIMIT 5;"; \
		echo "\n--- Top 5 Tagesprofile (inkl. Grundlast) ---"; \
		sqlite3 $(SQLITE_DB) "SELECT * FROM sensor_daily LIMIT 5;"; \
	else \
		echo "⚠️ Keine Datenbank unter $(SQLITE_DB) gefunden. Starte mit 'make run'."; \
	fi

# ---------------------------------------------------------
# 🐋 DOCKER AUTOMATION
# ---------------------------------------------------------
build:
	docker compose build

up:
	docker compose up -d
	@echo "✅ Container gestartet. Nutze 'make logs-tail' zum Mitlesen."

down:
	docker compose down

restart:
	docker compose restart

rebuild:
	docker compose down
	docker compose build --no-cache
	docker compose up -d --force-recreate

logs:
	docker compose logs

logs-tail:
	docker compose logs -f

ps:
	docker compose ps

stop:
	docker compose stop

start:
	docker compose start

shell:
	docker compose exec -it energy-analytics /bin/sh

health:
	@echo "🔍 Überprüfe Container-Status für $(CONTAINER)..."
	@docker inspect --format='{{json .State.Health}}' $(CONTAINER) || echo "Kein Healthcheck definiert."

clean:
	@echo "🧹 Bereinige temporäre Dateien..."
	rm -f $(LOG_FILE)
	rm -f $(SQLITE_DB)
	find . -type d -name "__pycache__" -exec rm -rf {} +

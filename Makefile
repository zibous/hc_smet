# Makefile for hc_scale (home-miscale)

.DEFAULT_GOAL := help
.PHONY: build up down restart rebuild logs ps run dev install clean backup help

# ---------------------------------------------------------
# Python interpreter (venv preferred, fallback python3)
# ---------------------------------------------------------
CONTAINER := $(shell basename $(CURDIR))
PYTHON := $(shell if [ -f /dockerapps/apps_v2/.venv/bin/python ]; then echo /dockerapps/apps_v2/.venv/bin/python; else echo python3; fi)

# ---------------------------------------------------------
# Lokales Ausfuehren
# ---------------------------------------------------------
run: ## Startet lokal mit uvicorn
	@PYTHONPATH=$(CURDIR) $(PYTHON) -m uvicorn app.main:app --host 0.0.0.0 --port 5056

dev: ## Startet lokal mit auto-reload
	@PYTHONPATH=$(CURDIR) $(PYTHON) -m uvicorn app.main:app --host 0.0.0.0 --port 5056 --reload

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

ps: ## Running containers
	docker compose ps

# ---------------------------------------------------------
# Maintenance
# ---------------------------------------------------------
install: ## Install dependencies
	@pip install -r requirements.txt

clean: ## Remove cache files
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -name "*.pyc" -delete 2>/dev/null || true

backup: ## Backup database
	@cp data/miscaledata.db data/miscaledata.db.bak.$$(date +%Y%m%d) 2>/dev/null && \
		echo "✅ Backup: data/miscaledata.db.bak.$$(date +%Y%m%d)" || \
		echo "❌ Keine DB gefunden"

data-add: ## Simuliert eine Messung: make data-add USER=Peter WEIGHT=69.5
	@PYTHONPATH=$(CURDIR) $(PYTHON) scripts/simulate_post.py --user $(or $(USER),Peter) --weight $(or $(WEIGHT),69.5) --impedance $(or $(IMPEDANCE),580)

data-remove: ## Entfernt letzten Eintrag: make data-remove USER=Peter
	@PYTHONPATH=$(CURDIR) $(PYTHON) scripts/simulate_post.py --remove --user $(or $(USER),Peter)

graph:
	pyreverse app -o png

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

# -*- coding: utf-8 -*-
"""hc_smet – SmartMeter PoKeys Service (FastAPI App)."""

import logging
import traceback
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from app.core.app_config import settings
from app.core.middleware import setup_middleware
from app.core.logging_setup import setup_logging
from app.services.startup import init_database, start_data_services, start_webhook

# Logging (einmal!)
setup_logging()
logger = logging.getLogger(__name__)
logger.info("Start Application")


# =================================================================
# LIFESPAN
# =================================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Lifespan: Modus = %s", settings.POKEY_SERVICE)

    # 1. Datenbank
    init_database()

    # 2. Daten-Services (PoKeys/SensorStore + MQTT)
    pokeys_manager, polling_stop_event, mqtt_publisher = start_data_services(app)

    # 3. Webhook Publisher
    webhook_publisher = start_webhook(pokeys_manager)

    logger.info("Lifespan: Infrastruktur erfolgreich gestartet.")
    yield

    # Shutdown
    logger.info("Lifespan: Shutdown...")
    if webhook_publisher:
        webhook_publisher.stop()
    try:
        from app.core.webhook import notify_ha
        notify_ha("app_stop", mode=settings.POKEY_SERVICE)
    except Exception:
        pass
    if polling_stop_event:
        polling_stop_event.set()
    if mqtt_publisher:
        mqtt_publisher.stop()
    logger.info("Lifespan: Beendet.")


# =================================================================
# FastAPI App
# =================================================================
app = FastAPI(lifespan=lifespan)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled Exception auf %s:\n%s", request.url.path, traceback.format_exc())
    return PlainTextResponse("Internal Server Error", status_code=500)


setup_middleware(app)

# =================================================================
# Static Files
# =================================================================
PROJECT_ROOT = Path(__file__).resolve().parent.parent
static_dir = PROJECT_ROOT / "frontend" / "static"
static_dir.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# =================================================================
# Router
# =================================================================
from app.api.base import router as base_router
from app.api.dashboard import router as dashboard_router
from app.api.dashboard2 import router as dashboard2_router
from app.api.kpi import router as kpi_router
from app.api.settingsdata import router as settings_router

app.include_router(base_router)
app.include_router(dashboard_router)
app.include_router(dashboard2_router)
app.include_router(kpi_router)
app.include_router(settings_router)

if settings.POKEY_SERVICE.upper() != "GET":
    from app.api.parsdecoder import router as parsdecoder_router
    app.include_router(parsdecoder_router)
    logger.info("Router: parsdecoder (POST) registriert.")
else:
    logger.info("Router: parsdecoder (POST) DEAKTIVIERT (GET-Modus aktiv).")


@app.get("/live", response_class=HTMLResponse, include_in_schema=False)
async def live_page(request: Request):
    from fastapi.templating import Jinja2Templates
    tpl_dir = str(PROJECT_ROOT / "frontend" / "templates")
    return Jinja2Templates(directory=tpl_dir).TemplateResponse(request=request, name="index2.html")

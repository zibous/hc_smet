# -*- coding: utf-8 -*-
"""
home-miscale – FastAPI Application
====================================
ESP32 (ESPHome) → HTTP POST → FastAPI → Berechnung → SQLite + MQTT → Home Assistant
"""

import atexit
import json
import logging
import os
import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse

from app.api.routes.appstatus import init_appstatus
from app.api.routes.appstatus import router as appstatus_router
from app.api.routes.dashboard import init_dashboard
from app.api.routes.dashboard import router as dashboard_router
from app.api.routes.health import router as health_router
from app.api.routes.miscale import init_services
from app.api.routes.miscale import router as miscale_router
from app.core.config import cfg
from app.core.heartbeat import Heartbeat
from app.core.logging import setup_logger
from app.core.mqtt import MqttClient
from app.core.shutdown import ShutdownManager
from app.models.user_service import UserService
from app.services.calcdata import CalcData
from app.services.db_manager import DBManager
from app.services.ha_discovery import publish_discovery_all

log = setup_logger("main")

# Services
user_service = UserService()
db = DBManager()
mqtt_client = MqttClient()
shutdown_mgr = ShutdownManager(log)


def _cleanup():
    if shutdown_mgr.is_set():
        return
    log.info("Cleanup gestartet")
    shutdown_mgr._event.set()
    for cb in shutdown_mgr._callbacks:
        try:
            cb()
        except Exception:
            pass


atexit.register(_cleanup)


# Health-Check Log Filter
class _HealthFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        msg = record.getMessage()
        if "/api/health" in msg or "Invalid HTTP request" in msg:
            return False
        return True


logging.getLogger("uvicorn.access").addFilter(_HealthFilter())
logging.getLogger("uvicorn.error").addFilter(_HealthFilter())


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup und Shutdown."""
    log.info("%s v%s starting on port %d", cfg.app_name, cfg.app_version, cfg.port)

    # Services in Routes injizieren
    init_services(user_service, db, mqtt_client)
    init_appstatus(mqtt_client)
    init_dashboard(db)

    # Heartbeat starten
    if mqtt_client.ready:
        heartbeat = Heartbeat(mqtt_client, cfg.mqtt.heartbeat, log, shutdown_mgr, cfg.mqtt.keepalive)
        heartbeat.start()
        shutdown_mgr.register(heartbeat.stop)
        log.info("Heartbeat gestartet → %s", cfg.mqtt.heartbeat)

        # HA Discovery + letzte Messwerte im Hintergrund
        def _mqtt_startup():
            try:
                users = user_service.all_users()
                publish_discovery_all(mqtt_client, [u.name for u in users])

                for user in users:
                    path = os.path.join(cfg.data_dir, f"miscale-{user.name}.json")
                    if not os.path.isfile(path):
                        continue
                    with open(path, "r") as f:
                        data = json.load(f)

                    topic_data = f"{cfg.mqtt.topic}/{user.name}/data"
                    mqtt_client.publish(topic_data, data, retain=True)

                    try:
                        calc = CalcData(user, data["weight"], data.get("impedance", 500), data.get("timestamp", ""))
                        calc.calculate()
                        scores = calc.calculate_scores()
                        mqtt_client.publish(f"{cfg.mqtt.topic}/{user.name}/scores", scores, retain=True)
                    except Exception:
                        log.exception("Scores-Berechnung fehlgeschlagen für %s", user.name)

                log.info("MQTT Startup abgeschlossen")
            except Exception:
                log.exception("MQTT Startup fehlgeschlagen")

        threading.Thread(target=_mqtt_startup, daemon=True, name="mqtt-startup").start()
    else:
        log.warning("MQTT nicht verfügbar – Heartbeat und HA Discovery deaktiviert")

    log.info("App initialisiert")
    yield
    log.info("%s shutting down", cfg.app_name)
    shutdown_mgr.initiate()


app = FastAPI(
    title=cfg.app_name,
    version=cfg.app_version,
    root_path=os.environ.get("ROOT_PATH", ""),
    lifespan=lifespan,
)

# Routes
app.include_router(health_router, prefix="/api", tags=["health"])
app.include_router(appstatus_router, prefix="/api", tags=["status"])
app.include_router(miscale_router, prefix="", tags=["miscale"])
app.include_router(dashboard_router, prefix="", tags=["dashboard"])


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Dashboard HTML."""
    from pathlib import Path

    from fastapi.templating import Jinja2Templates

    templates = Jinja2Templates(directory=str(Path(__file__).parent.parent / "frontend"))
    base_url = str(request.scope.get("root_path", ""))
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "app_title": cfg.app_title,
            "base_url": base_url,
        },
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host=cfg.host, port=cfg.port, reload=True)

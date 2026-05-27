import logging
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
import traceback

from app.core.app_config import settings
from app.core.middleware import setup_middleware
from app.core.logging_setup import setup_logging

from app.api.base import router as base_router
from app.api.dashboard import router as dashboard_router
from app.api.dashboard2 import router as dashboard2_router
from app.api.settingsdata import router as settings_router

from app.infrastructure.database.dbconnect import Database
from app.services.pokeys_manager import PoKeysManager, start_polling_thread

# Logging Setup (nur einmal!)
setup_logging()
logger = logging.getLogger(__name__)

logger.info("Start Application")

# =================================================================
# LIFESPAN: Sicheres Initialisieren der DB-Infrastruktur beim Start
# =================================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Lifespan: Initialisiere Datenbank-Infrastruktur...")
    logger.info(f"Lifespan: POKEY_SERVICE Modus = {settings.POKEY_SERVICE}")

    # Datenbank-Singleton mit dem dynamischen Pfad aus den Settings erzeugen
    db_path = settings.database_path / settings.database_name
    Database(str(db_path))

    # hourly_values Tabelle sicherstellen
    conn = Database._instance.get_conn()
    try:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS hourly_values (
                sensor_id TEXT NOT NULL,
                hour INTEGER NOT NULL,
                consumption REAL NOT NULL,
                total REAL,
                PRIMARY KEY (sensor_id, hour)
            );
            CREATE INDEX IF NOT EXISTS idx_hour ON hourly_values(hour);
        """)
    finally:
        conn.close()

    # --- MODUS-WEICHE: GET vs POST ---
    pokeys_manager = None
    polling_stop_event = None
    mqtt_publisher = None

    if settings.POKEY_SERVICE.upper() == "GET":
        # ============================================================
        # GET-MODUS: PoKeysManager + Polling-Thread
        # ============================================================
        logger.info("Lifespan: Starte GET-Modus (NetworkClient Polling)...")
        pokeys_manager = PoKeysManager()
        polling_stop_event = start_polling_thread(
            pokeys_manager, interval=settings.FETCH_INTERVAL
        )
        # Manager global verfügbar machen
        app.state.pokeys_manager = pokeys_manager

        # MQTT Publisher mit PoKeysManager als Datenquelle
        if settings.MQTT_ENABLED:
            from app.services.mqtt_publisher import MQTTPublisher
            mqtt_publisher = MQTTPublisher(pokeys_manager)
            mqtt_publisher.start()

    else:
        # ============================================================
        # POST-MODUS: Legacy SensorStore (bisheriges Verhalten)
        # ============================================================
        logger.info("Lifespan: Starte POST-Modus (Legacy parsdecoder)...")
        from app.api.parsdecoder import _shared_store
        json_exists = _shared_store.file_path.exists()
        logger.info(f"Lifespan: sensor_state.json existiert: {json_exists}")
        if not json_exists:
            _shared_store._cleanup_import_hour()

        # MQTT Publisher mit SensorStore als Datenquelle
        if settings.MQTT_ENABLED:
            from app.services.mqtt_publisher import MQTTPublisher
            mqtt_publisher = MQTTPublisher(_shared_store)
            mqtt_publisher.start()

    # Webhook Publisher starten (unabhängig vom Modus)
    from app.core.webhook import WebhookPublisher
    webhook_publisher = WebhookPublisher()
    webhook_publisher.start()

    logger.info("Lifespan: Infrastruktur erfolgreich gestartet.")
    yield

    # Shutdown
    if polling_stop_event:
        polling_stop_event.set()
        logger.info("Lifespan: Polling-Thread gestoppt.")
    webhook_publisher.stop()
    if mqtt_publisher:
        mqtt_publisher.stop()
    logger.info("Lifespan: App wird heruntergefahren.")

# =================================================================
# FastAPI App (inklusive Lifespan)
# =================================================================
app = FastAPI(lifespan=lifespan)

# Globaler Exception-Handler: Loggt den vollständigen Traceback
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled Exception auf {request.url.path}:\n{traceback.format_exc()}")
    return PlainTextResponse("Internal Server Error", status_code=500)

# Middleware registrieren
setup_middleware(app)

# =================================================================
# Static Files (KORRIGIERT: Wechselt in die Projekt-Root)
# =================================================================
BASE_DIR = Path(__file__).resolve().parent  # /dockerapps/apps_v2/hc_smet/app
PROJECT_ROOT = BASE_DIR.parent              # /dockerapps/apps_v2/hc_smet

static_dir = PROJECT_ROOT / "frontend" / "static"

# Sicherheitscheck: Ordner anlegen falls nicht vorhanden
if not static_dir.exists():
    logger.warning(f"Statischer Ordner nicht gefunden, erstelle: {static_dir}")
    static_dir.mkdir(parents=True, exist_ok=True)

app.mount(
    "/static",
    StaticFiles(directory=str(static_dir)),
    name="static"
)

# =================================================================
# Router registrieren
# =================================================================
app.include_router(base_router)

app.include_router(dashboard_router)

app.include_router(dashboard2_router)

# POST-Endpoint NUR im POST-Modus registrieren (Kollisionsschutz)
if settings.POKEY_SERVICE.upper() != "GET":
    from app.api.parsdecoder import router as parsdecoder_router
    app.include_router(parsdecoder_router)
    logger.info("Router: parsdecoder (POST) registriert.")
else:
    logger.info("Router: parsdecoder (POST) DEAKTIVIERT (GET-Modus aktiv).")

app.include_router(settings_router)

# =================================================================
# Separate HTML-Route für /live (ohne API-Prefix)
# =================================================================
@app.get("/live", response_class=HTMLResponse, include_in_schema=False)
async def live_page(request: Request):
    from fastapi.templating import Jinja2Templates
    from pathlib import Path
    _tpl = Jinja2Templates(directory=str(Path(__file__).resolve().parent.parent / "frontend" / "templates"))
    return _tpl.TemplateResponse(request=request, name="index2.html")

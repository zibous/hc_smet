import logging
import time
import shutil
from pathlib import Path
from fastapi import APIRouter, Request, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

# 🔧 ZENTRALE IMPORTE
from app.core.app_config import settings
from app.schemas.settings import SettingsSchema
from app.infrastructure.database.dbconnect import Database

# Optional für System-Metriken (CPU/RAM)
try:
    import psutil
except ImportError:
    psutil = None

logger = logging.getLogger(__name__)
router = APIRouter(tags=["System & Configuration"])

# START TIME für die Uptime-Berechnung festhalten
APP_START_TIME = time.time()

# =================================================================
# 🔧 PORTABLE TEMPLATE-LOCATION
# =================================================================
template_dir = settings.database_path.parent / "frontend" / "templates"

if not template_dir.exists():
    logger.error(f"❌ KRITISCH: Template-Ordner nicht gefunden unter: {template_dir}")

templates = Jinja2Templates(directory=str(template_dir))


# =================================================================
# HELPER: System- & Health-Informationen ermitteln
# =================================================================
def get_system_health() -> dict:
    uptime_seconds = int(time.time() - APP_START_TIME)
    days, rem = divmod(uptime_seconds, 86400)
    hours, rem = divmod(rem, 3600)
    minutes, seconds = divmod(rem, 60)
    uptime_str = f"{days}d {hours}h {minutes}m {seconds}s" if days > 0 else f"{hours}h {minutes}m {seconds}s"

    db_dir = settings.database_path
    try:
        total, used, free = shutil.disk_usage(db_dir)
        disk_free_gb = round(free / (1024 ** 3), 2)
        disk_used_pct = round((used / total) * 100, 1)
    except Exception:
        disk_free_gb, disk_used_pct = 0.0, 0.0

    db_healthy = False
    db_error = None
    if Database._instance:
        try:
            conn = Database._instance.get_conn()
            conn.execute("SELECT 1;").fetchone()
            conn.close()
            db_healthy = True
        except Exception as e:
            db_error = str(e)
    else:
        db_error = "Datenbank-Singleton nicht initialisiert."

    cpu_usage = psutil.cpu_percent() if psutil else "N/A"
    ram_usage = psutil.virtual_memory().percent if psutil else "N/A"

    log_file = Path(settings.LOG_FILE)
    if not log_file.is_absolute():
        log_file = (settings.database_path.parent / log_file).resolve()

    error_count = 0
    if log_file.exists():
        try:
            with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()[-100:]
                error_count = sum(1 for line in lines if "ERROR" in line or "CRITICAL" in line)
        except Exception:
            pass

    return {
        "status": "healthy" if db_healthy and (disk_used_pct < 95 if disk_used_pct > 0 else True) else "unhealthy",
        "timestamp": int(time.time()),
        "uptime": uptime_str,
        "database": {
            "connected": db_healthy,
            "file": settings.database_name,
            "error": db_error
        },
        "hardware": {
            "cpu_usage_pct": cpu_usage,
            "ram_usage_pct": ram_usage,
            "disk_free_gb": disk_free_gb,
            "disk_used_pct": disk_used_pct
        },
        "logs": {
            "recent_errors_count": error_count,
            "log_file_path": str(log_file)
        }
    }


# =================================================================
# JSON ENDPUNKT (Für automatisierte Überwachung / Monitoring)
# =================================================================
@router.get("/api/status")
async def api_status():
    """Liefert den detaillierten Gesundheitszustand des Ökosystems für Monitoring-Tools."""
    health_data = get_system_health()
    status_code = status.HTTP_200_OK if health_data["status"] == "healthy" else status.HTTP_503_SERVICE_UNAVAILABLE
    return JSONResponse(content=health_data, status_code=status_code)


# =================================================================
# HTML ENDPUNKT (Schöne Status-Oberfläche für den Browser)
# =================================================================
@router.get("/status", response_class=HTMLResponse)
async def status_view(request: Request):
    """Rendert den System- & Hardwarezustand als Weboberfläche."""
    return templates.TemplateResponse(
        request=request,
        name="status.html",
        context={
            "health": get_system_health()
        }
    )


# =================================================================
# SETTINGS HTML VIEW ENDPUNKT
# =================================================================
@router.get("/settings", response_class=HTMLResponse)
async def settings_view(request: Request):
    """Rendert die Live-Konfiguration der Anwendung in der HTML-Schablone."""
    settings_dict = settings.model_dump()

    settings_dict.update({
        "database_name": settings.database_name,
        "database_path": str(settings.database_path),
        "analytics_db_path": str(settings.analytics_db_path),
        "mqtt_mode": settings.mqtt_mode,
        "mqtt_topic_sensors": settings.mqtt_topic_sensors,
        "mapping_file": str(settings.mapping_file),
    })

    return templates.TemplateResponse(
        request=request,
        name="settings.html",
        context={
            "settings": settings_dict
        }
    )


# =================================================================
# JSON SETTINGS ENDPUNKT (Für Swagger /docs Integration)
# =================================================================
@router.get("/api/settings/json", response_model=SettingsSchema)
async def get_settings_json():
    """Gibt die komplette Live-Konfiguration strukturiert und voll dokumentiert als JSON aus."""
    logger.debug("Live-Settings via JSON angefordert")
    return settings


# =================================================================
# 🔍 LIVE-DIAGNOSE ENDPUNKT FÜR S01 - S50 (KORRIGIERT & GEHÄRTET)
# =================================================================
@router.get("/api/diagnose/sensors")
async def diagnose_sensors():
    """Gibt den aktuellen Live-Zustand aller 50 Sensoren aus dem RAM-Speicher aus."""
    from app.api.parsdecoder import _shared_store

    live_data = _shared_store.get_all()

    # Sortiert die Sensoren aufsteigend von S01 bis S50 für maximale Übersicht
    sorted_sensors = {}
    for k in sorted(live_data.keys()):
        entry = live_data[k]
        if hasattr(entry, "model_dump"):
            sorted_sensors[k] = entry.model_dump()
        else:
            sorted_sensors[k] = dict(entry)

    # 🔧 FIX: Ermittelt den Kalibrierungs-Zustand nun krisenfest direkt über die
    # Existenz der Datei oder ob der RAM-Speicher noch komplett unbefüllt ist.
    is_calibrating = not _shared_store.file_path.exists() or len(sorted_sensors) == 0

    return {
        "status": "active",
        "total_tracked_sensors": len(sorted_sensors),
        "fresh_start_calibration_active": is_calibrating,
        "timestamp_now": int(time.time()),
        "sensors": sorted_sensors
    }

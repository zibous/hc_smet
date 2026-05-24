import logging
import time
import os
from datetime import datetime
from pathlib import Path
import aiofiles  # Für asynchrones Schreiben ohne Blockieren
from fastapi import APIRouter, Request, Depends, status

from app.core.app_config import settings
from app.services.sensor_service import SensorService
from app.services.state.sensor_store import SensorStore

logger = logging.getLogger(__name__)
router = APIRouter(tags=["decode_post"])

_shared_store = SensorStore()

def get_sensor_service() -> SensorService:
    return SensorService(_shared_store)

async def log_post_to_file(device: str, body: bytes):
    """Schreibt UTC-Sekunden, lokale Zeit und den Body asynchron in eine Datei."""
    try:
        # Bereinigt den User-Agent, um ungültige Dateinamen/Pfade zu verhindern
        safe_device = "".join(c for c in device if c.isalnum() or c in "._-").strip()
        if not safe_device:
            safe_device = "unknown_device"

        # Nutzt settings.LOG_DIR für den Pfad
        log_file = settings.LOG_DIR / f"{safe_device}.log"

        # Erstellt den Ordner aus den Settings, falls er noch nicht existiert
        settings.LOG_DIR.mkdir(parents=True, exist_ok=True)

        # Zeitstempel generieren
        utc_seconds = int(time.time())
        local_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Konvertiert Bytes in Text (Fallback zu latin-1, falls kein valides UTF-8)
        body_str = body.decode("utf-8", errors="replace").replace("\n", " ")

        # Asynchrones Anhängen (Append) an die Datei
        async with aiofiles.open(log_file, mode="a", encoding="utf-8") as f:
            await f.write(f"{utc_seconds}, {local_time}, {body_str}\n")

    except Exception as e:
        logger.error(f"Fehler beim Schreiben der Log-Datei für {device}: {e}")

@router.post("/", status_code=status.HTTP_200_OK)
async def receive(
    request: Request,
    service: SensorService = Depends(get_sensor_service)
):
    body = await request.body()
    device = request.headers.get("User-Agent")
    is_simulator = request.headers.get("X-Source") == "simulator"

    if not body:
        logger.warning("Abgewiesen: Eingehender POST-Body ist komplett leer.")
        return {"status": "empty body"}

    if not device:
        logger.warning("Abgewiesen: 'User-Agent' Header fehlt im HTTP-Request.")
        return {"status": "missing device"}

    # 💾 Logge Daten asynchron, wenn es KEIN Simulator ist und Logging aktiv ist
    if not is_simulator and settings.DATA_LOG_ENABELD:
        logger.debug(f"Logge Daten für Gerät {device}")
        await log_post_to_file(device, body)

    try:
        payload = body.decode("utf-8", errors="ignore")
    except Exception as e:
        logger.error(f"Kritisch: Payload-Dekodierung fehlgeschlagen: {e}")
        return {"status": "invalid encoding"}

    if not payload:
        return {"status": "missing payload"}

    result = service.handle(
        device=device,
        payload=payload,
        simulator=is_simulator,
        skip_db=False
    )

    if is_simulator and result:
        sensor_count = len(result)
        now = int(time.time())
        sample = list(result.items())[:2]

        logger.debug(
            f"\n========================================\n"
            f"📡 POKEYS INPUT DETEKTIERT (SIMULATOR)\n"
            f"📦 GERÄT: {device}\n"
            f"📊 VERARBEITETE SENSOREN: {sensor_count}\n"
            f"⏱️  SYSTEM-ZEITSTEMPEL: {now}\n"
            f"🔎 COMPACT SAMPLE: {sample}\n"
            f"========================================"
        )

    return {"status": "ok"}

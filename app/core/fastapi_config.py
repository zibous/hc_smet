import hashlib
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# =================================================================
# KORREKTUR: Absoluten Pfad zur Projekt-Wurzel (Project-Root) ermitteln
# =================================================================
CURRENT_DIR = Path(__file__).resolve().parent  # app/core
PROJECT_ROOT = CURRENT_DIR.parent.parent       # Wechselt in die Projekt-Root (hc_smet)

def file_hash(relative_path: str) -> str:
    """Berechnet den MD5-Hash einer Datei speicherschonend über absolute Pfade.
    Liefert einen Fallback-Hash, falls die Datei nicht existiert.
    """
    absolute_path = PROJECT_ROOT / relative_path

    if not absolute_path.exists():
        logger.warning(f"Static-Datei für Cache-Busting nicht gefunden: {absolute_path}")
        return "default_v1"  # Sicherer Fallback, damit die App nicht crasht

    # Speicherschonendes Einlesen in kleinen 4KB-Blöcken (Chunking)
    hasher = hashlib.md5()
    try:
        with absolute_path.open("rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)
        return hasher.hexdigest()[:10]
    except Exception as e:
        logger.error(f"Fehler beim Berechnen des Datei-Hashes für {absolute_path}: {e}")
        return "error_v1"

# =================================================================
# STATIC VERSIONEN FÜR CACHE-BUSTING
# =================================================================
# Nutzt jetzt die sicheren, absoluten Pfade ausgehend von der Root
STATIC_VERSION = {
    "app_js": file_hash("frontend/static/js/main.js"),
    "style_css": file_hash("frontend/static/css/style.css"),
}

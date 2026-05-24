import logging
import logging.config
from pathlib import Path
from app.core.app_config import settings

def setup_logging():
    """Initialisiert das Logging-System dynamisch basierend auf den App-Settings."""

    # Sicherstellen, dass das Log-Verzeichnis existiert
    log_file_path = Path(settings.LOG_FILE)
    if not log_file_path.is_absolute():
        # Falls relativ deklariert, relativ zur Projekt-Root auflösen
        log_file_path = (Path(__file__).resolve().parent.parent.parent / log_file_path).resolve()

    log_file_path.parent.mkdir(parents=True, exist_ok=True)

    # Bestimmen, welche Handler aktiv sein sollen ("console", "file" oder "both")
    active_handlers = []
    log_mode = settings.LOG_MODE.lower()

    if log_mode in ("console", "both"):
        active_handlers.append("console")
    if log_mode in ("file", "both"):
        active_handlers.append("file")

    # Falls die Eingabe fehlerhaft war, mindestens Console aktivieren
    if not active_handlers:
        active_handlers = ["console"]

    LOGGING_CONFIG = {
        "version": 1,
        "disable_existing_loggers": False,

        "formatters": {
            "standard": {
                "format": "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            }
        },

        "handlers": {
            # 1. Console Handler
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "standard",
                "stream": "ext://sys.stdout",
            },
            # 2. File Handler mit automatischer Rotation (Sicherheit gegen volle Festplatten)
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "formatter": "standard",
                "filename": str(log_file_path),
                "maxBytes": 5 * 1024 * 1024,  # 5 MB pro Datei
                "backupCount": 3,             # Behalte maximal 3 alte Log-Dateien
                "encoding": "utf-8",
            }
        },

        # Root-Logger nutzt das dynamische Level und die aktiven Handler aus den Settings
        "root": {
            "handlers": active_handlers,
            "level": settings.LOG_LEVEL.upper(),
        },

        "loggers": {
            # Uvicorn-Logger anpassen, damit sie nicht doppelt loggen (propagate=False)
            "uvicorn": {
                "handlers": active_handlers,
                "level": "CRITICAL",
                "propagate": False,
            },
            "uvicorn.error": {
                "handlers": active_handlers,
                "level": "CRITICAL",
                "propagate": False,
            },
            "uvicorn.access": {
                "handlers": active_handlers,
                "level": "CRITICAL",
                "propagate": False,
            },
        },
    }

    logging.config.dictConfig(LOGGING_CONFIG)

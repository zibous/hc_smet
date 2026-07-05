# -*- coding: utf-8 -*-
"""Startup-Logik für hc_smet – ausgelagert aus main.py."""

import logging
from typing import Optional, Tuple

from fastapi import FastAPI

from app.core.app_config import settings
from app.infrastructure.database.dbconnect import Database
from app.services.pokeys_manager import PoKeysManager, start_polling_thread

logger = logging.getLogger(__name__)


def init_database():
    """Initialisiert die SQLite-Datenbank und stellt Tabellen sicher."""
    db_path = settings.database_path / settings.database_name
    Database(str(db_path))

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

    logger.info("Datenbank initialisiert: %s", db_path)


def start_data_services(app: FastAPI) -> Tuple[Optional[PoKeysManager], Optional[object], Optional[object]]:
    """Startet PoKeys/SensorStore + MQTT je nach Modus.

    Returns:
        (pokeys_manager, polling_stop_event, mqtt_publisher)
    """
    pokeys_manager = None
    polling_stop_event = None
    mqtt_publisher = None

    if settings.POKEY_SERVICE.upper() == "GET":
        logger.info("Starte GET-Modus (NetworkClient Polling)...")
        pokeys_manager = PoKeysManager()
        polling_stop_event = start_polling_thread(pokeys_manager, interval=settings.FETCH_INTERVAL)
        app.state.pokeys_manager = pokeys_manager

        if settings.MQTT_ENABLED:
            from app.services.mqtt_publisher import MQTTPublisher
            mqtt_publisher = MQTTPublisher(pokeys_manager)
            mqtt_publisher.start()

    else:
        logger.info("Starte POST-Modus (Legacy parsdecoder)...")
        from app.api.parsdecoder import _shared_store
        if not _shared_store.file_path.exists():
            _shared_store._cleanup_import_hour()

        if settings.MQTT_ENABLED:
            from app.services.mqtt_publisher import MQTTPublisher
            mqtt_publisher = MQTTPublisher(_shared_store)
            mqtt_publisher.start()

    return pokeys_manager, polling_stop_event, mqtt_publisher


def start_webhook(pokeys_manager: Optional[PoKeysManager] = None):
    """Startet den Webhook Publisher. Gibt Publisher zurück oder None bei Fehler."""
    try:
        from app.core.webhook import WebhookPublisher, notify_ha
        from app.services.webhook_builder import build_heartbeat, build_daily, build_monthly

        publisher = WebhookPublisher(
            build_heartbeat=lambda: build_heartbeat(pokeys_manager),
            build_daily=build_daily,
            build_monthly=build_monthly,
        )
        publisher.start()
        notify_ha("app_start", mode=settings.POKEY_SERVICE)
        return publisher

    except Exception as e:
        logger.warning("Webhook-Setup fehlgeschlagen (App läuft weiter): %s", e)
        return None

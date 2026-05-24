import logging
import time
from typing import Any

from app.core.app_config import settings
from app.infrastructure.parsers.parsePostdata import get_postData
from app.schemas.sensors import IncomingSensorData

logger = logging.getLogger(__name__)


class SensorService:
    """Verarbeitet eingehende PoKeys-Daten.

    Der SensorStore übernimmt Delta-Berechnung und DB-Schreibvorgänge direkt.
    Kein separater Aggregator mehr nötig.
    """

    def __init__(self, store):
        self.store = store

    def handle(self, device: str, payload: Any, simulator: bool = False, skip_db: bool = False) -> dict[str, dict]:

        """Verarbeitet die eingehenden PoKeys-Daten."""
        logger.debug(f"Sensor Service call for {device} (Skip DB: {skip_db})")

        index = settings.get_devices_start_index(device)
        raw_data = get_postData(payload, index=index)

        normalized_result = {}
        store_payload = {}
        now_ts = int(time.time())

        for sensor_id, raw_value in raw_data.items():
            if raw_value is None:
                continue

            payload_dict = {
                "current": float(raw_value),
                "timestamp": now_ts
            }

            try:
                validated = IncomingSensorData.model_validate(payload_dict)
                normalized_result[sensor_id] = validated.model_dump()
                store_payload[sensor_id] = float(raw_value)
            except Exception as e:
                logger.error(f"❌ Validierungsfehler bei Sensor {sensor_id}: {e}")
                continue

        if not store_payload:
            return {}

        # SensorStore berechnet Deltas und schreibt direkt in die DB
        if skip_db:
            # Temporär DB deaktivieren für diesen Aufruf
            old_db = self.store.db_enabled
            self.store.db_enabled = False
            self.store.update(store_payload)
            self.store.db_enabled = old_db
            logger.info(f"🛡️ DB-Schreibvorgang übersprungen für {device}.")
        else:
            self.store.update(store_payload)

        return normalized_result

    def get_all(self):
        return self.store.get_all()

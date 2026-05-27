# -*- coding: utf-8 -*-
"""StorageHandler — Atomare JSON-Persistenz für Sensor-States.

Speichert und lädt alle Sensorwerte in/aus einer JSON-Datei.
Atomares Schreiben via tempfile + os.replace() verhindert Datenverlust bei Crashes.

WICHTIG bei Device-Neustart:
Fällt der Wert in der sensorList.json plötzlich von z.B. 15000 auf 0 zurück,
erkennt die S0Sensor.update()-Methode den Geräteneustart und setzt den Wert
lautlos auf den neuen Stand. Der persistierte total_kwh bleibt erhalten.
"""

import json
import logging
import os
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)


class StorageHandler:
    """Persistente JSON-Speicherung mit atomarem Schreiben."""

    def __init__(self, filepath: Path | str):
        """
        Args:
            filepath: Absoluter Pfad zur JSON-Datei
        """
        self.filepath = Path(filepath)

    def load(self, sensors: dict) -> None:
        """Lädt persistierte Werte in die Sensor-Objekte.

        Args:
            sensors: Dict von sensor_id → S0Sensor-Instanz
        """
        if not self.filepath.exists():
            logger.info(f"Keine persistente Datei gefunden: {self.filepath.name} (Erststart)")
            return

        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                data = json.load(f)

            loaded_count = 0
            for sid, sensor in sensors.items():
                if sid in data:
                    sensor.load_dict(data[sid])
                    loaded_count += 1

            logger.info(f"✅ {loaded_count} Sensoren aus {self.filepath.name} geladen.")

        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.warning(f"⚠️ Fehler beim Laden von {self.filepath.name}: {e}")

    def save(self, sensors: dict) -> None:
        """Speichert alle Sensor-States atomar in die JSON-Datei.

        Verwendet tempfile + os.replace() für Crash-Sicherheit:
        - Schreibt in temporäre Datei
        - fsync() für Disk-Flush
        - Atomares Rename (os.replace)

        Args:
            sensors: Dict von sensor_id → S0Sensor-Instanz
        """
        out = {sid: s.to_dict() for sid, s in sensors.items()}

        # Verzeichnis sicherstellen
        self.filepath.parent.mkdir(parents=True, exist_ok=True)
        dir_name = str(self.filepath.parent)

        fd, tmp_path = tempfile.mkstemp(dir=dir_name, suffix=".tmp")

        try:
            with os.fdopen(fd, "w", encoding="utf-8") as tmp_file:
                json.dump(out, tmp_file, indent=2)
                tmp_file.flush()
                os.fsync(tmp_file.fileno())

            os.replace(tmp_path, str(self.filepath))

        except Exception as e:
            logger.error(f"❌ Fehler beim Speichern von {self.filepath.name}: {e}")
            try:
                os.remove(tmp_path)
            except OSError:
                pass
            raise

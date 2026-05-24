import json
import logging
import time
import sqlite3
from pathlib import Path
from threading import Lock
from pydantic import TypeAdapter

from app.schemas.sensors import SensorStateEntry
from app.infrastructure.database.dbconnect import Database

logger = logging.getLogger(__name__)


class SensorStore:
    """Zentraler State-Manager für alle Sensoren.

    Verantwortlich für:
    - RAM-State (current, last, delta, timestamp)
    - Persistenz nach sensor_state.json
    - Direktes Schreiben der Deltas in hourly_values (SQLite)
    - Gleichmäßige Verteilung bei Zeitlücken > 1h
    """

    def __init__(self, file_path=None, use_file=True, db_enabled=True):
        from app.core.app_config import settings
        self.use_file = use_file
        self.db_enabled = db_enabled
        self.file_path = Path(file_path) if file_path else (settings.DATA_DIR / "sensor_state.json")
        self.scale_factor = settings.SENSOR_SCALE_FACTOR
        self.trace_enabed = settings.DATA_TRACE_ENABELD
        self.data: dict[str, SensorStateEntry] = {}
        self._adapter = TypeAdapter(dict[str, SensorStateEntry])
        self._lock = Lock()

        # In-Memory Register für bekannte Kanäle seit Anwendungsstart
        self._calibrated_sensors: set[str] = set()

        if self.use_file:
            self._load()

    # =========================================================
    # LOAD / SAVE (JSON Persistenz)
    # =========================================================
    def _load(self):
        """Lädt den letzten bekannten State aus sensor_state.json."""
        if not self.file_path.exists():
            logger.warning(f"ℹ️ {self.file_path.name} fehlt auf der Festplatte. Erststart-Kalibrierungsschutz aktiv.")
            return
        try:
            raw_json = json.loads(self.file_path.read_text(encoding="utf-8"))
            self.data = self._adapter.validate_python(raw_json)
            self._calibrated_sensors = set(self.data.keys())
            logger.info(f"✅ {len(self.data)} Sensoren erfolgreich aus sensor_state.json geladen.")
        except Exception as e:
            logger.error(f"⚠️ sensor_state.json war korrupt! Initialisiere leeren RAM-Speicher: {e}")
            self.data = {}

    def _cleanup_import_hour(self):
        """Löscht die letzte (unvollständige) Import-Stunde aus hourly_values.

        Beim frischen Start nach einem Import ist die letzte Stunde in der DB
        nur teilweise befüllt. Wenn die App in der gleichen Stunde startet,
        würde sie draufaddieren → Doppelbuchung. Deshalb löschen wir die
        letzte Stunde komplett — die App füllt sie dann sauber neu.
        """
        if not self.db_enabled or Database._instance is None:
            return
        try:
            conn = Database._instance.get_conn()
            row = conn.execute("SELECT MAX(hour) FROM hourly_values").fetchone()
            if row and row[0]:
                max_hour = row[0]
                now_ts = int(time.time())
                current_hour = (now_ts // 3600) * 3600

                # Nur löschen wenn die letzte Import-Stunde = aktuelle Stunde
                if max_hour >= current_hour:
                    conn.execute("DELETE FROM hourly_values WHERE hour = ?", (max_hour,))
                    conn.commit()
                    logger.info(f"🧹 Import-Stunde {max_hour} gelöscht (Überlapp-Schutz).")
            conn.close()
        except Exception as e:
            logger.warning(f"⚠️ Cleanup der Import-Stunde fehlgeschlagen: {e}")

    def _try_recover_from_db(self):
        """Versucht den letzten Zählerstand aus hourly_values.total zu lesen (Fallback)."""
        if not self.db_enabled or Database._instance is None:
            return
        try:
            conn = Database._instance.get_conn()
            rows = conn.execute("""
                SELECT sensor_id, total
                FROM hourly_values
                WHERE total IS NOT NULL
                GROUP BY sensor_id
                HAVING hour = MAX(hour)
            """).fetchall()
            conn.close()

            if rows:
                now_ts = int(time.time())
                for sensor_id, total in rows:
                    if total and total > 0:
                        self.data[sensor_id] = SensorStateEntry(
                            current=total, last=total, delta=0.0, timestamp=now_ts
                        )
                        self._calibrated_sensors.add(sensor_id)
                logger.info(f"🔄 {len(rows)} Sensoren aus DB (total-Spalte) wiederhergestellt.")
        except Exception as e:
            logger.warning(f"⚠️ DB-Recovery fehlgeschlagen: {e}")

    def _save(self):
        """Persistiert den aktuellen RAM-State atomar nach sensor_state.json."""
        if not self.use_file:
            return
        try:
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self.file_path.with_suffix(".tmp")
            serialized = self._adapter.dump_json(self.data, indent=2).decode("utf-8")
            tmp.write_text(serialized, encoding="utf-8")
            tmp.replace(self.file_path)
        except Exception as e:
            logger.error(f"❌ Schwerwiegender I/O-Fehler beim Schreiben der sensor_state.json: {e}")

    # =========================================================
    # DB WRITE (hourly_values)
    # =========================================================
    def _db_add_hour(self, sensor_id: str, hour: int, delta: float, total: float):
        """Schreibt ein Delta in hourly_values (addiert auf bestehenden Wert).

        Ermittelt das Jahr automatisch aus dem hour-Timestamp und nutzt
        die entsprechende Jahres-Datenbank (sensors_YYYY.db).
        """
        if not self.db_enabled or Database._instance is None:
            return
        try:
            from datetime import datetime, timezone
            year = datetime.fromtimestamp(hour, tz=timezone.utc).year

            conn = Database._instance.get_conn(year=year)

            # Tabelle sicherstellen (für neue Jahres-DBs)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS hourly_values (
                    sensor_id TEXT NOT NULL,
                    hour INTEGER NOT NULL,
                    consumption REAL NOT NULL,
                    total REAL,
                    PRIMARY KEY (sensor_id, hour)
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_hour ON hourly_values(hour)")

            conn.execute("""
                INSERT INTO hourly_values(sensor_id, hour, consumption, total)
                VALUES (?, ?, round(?, 6), ?)
                ON CONFLICT(sensor_id, hour) DO UPDATE SET
                    consumption = round(hourly_values.consumption + excluded.consumption, 6),
                    total = excluded.total
            """, (sensor_id, hour, delta, total))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"❌ DB-Schreibfehler für {sensor_id} (hour={hour}): {e}")

    # =========================================================
    # MAIN UPDATE (Hot Path)
    # =========================================================
    def update(self, new_data: dict) -> bool:
        """Verarbeitet eingehende Sensorwerte: Delta berechnen, RAM updaten, DB schreiben.

        Args:
            new_data: Dict mit sensor_id → Totalwert (float)

        Returns:
            True wenn erfolgreich
        """
        if not new_data:
            return False

        now_ts = int(time.time())
        current_hour = (now_ts // 3600) * 3600

        with self._lock:
            for key, raw_value in new_data.items():
                # Typ-Normalisierung
                if isinstance(raw_value, dict):
                    current = float(raw_value.get("current", 0.0))
                    ts = raw_value.get("timestamp", now_ts)
                else:
                    current = float(raw_value)
                    ts = now_ts

                current = round(current, 6)
                old_entry = self.data.get(key)

                # --- KALIBRIERUNG: Erster Kontakt ---
                if key not in self._calibrated_sensors or not old_entry:
                    self._calibrated_sensors.add(key)
                    self.data[key] = SensorStateEntry(
                        current=current, last=current, delta=0.0, timestamp=ts
                    )
                    logger.info(f"🛡️ Sensor {key} auf Basiswert initialisiert ({current} kWh).")
                    continue

                # --- ZÄHLER-RESET ---
                if current < old_entry.current:
                    logger.warning(f"🔄 Zähler-Reset detektiert für {key}: {old_entry.current} → {current}.")
                    self.data[key] = SensorStateEntry(
                        current=current, last=current, delta=0.0, timestamp=ts
                    )
                    continue

                # --- NORMALER WERT: Delta berechnen ---
                delta = round(current - old_entry.current, 6)

                # RAM aktualisieren
                self.data[key] = SensorStateEntry(
                    current=current, last=old_entry.current, delta=delta, timestamp=ts
                )

                # In DB schreiben (nur wenn delta > 0)
                if delta > 0:
                    time_diff = ts - old_entry.timestamp
                    # Scale-Faktor anwenden (PoKey sendet Wh, DB speichert kWh)
                    scaled_delta = round(delta * self.scale_factor, 6)

                    if time_diff <= 3600:
                        # Normaler Fall: Delta in die aktuelle Stunde buchen
                        self._db_add_hour(key, current_hour, scaled_delta, current)
                        # CSV-Trace für Verifikation
                        if self.trace_enabed:
                            self._trace_csv(key, ts, current, old_entry.current, delta, scaled_delta, current_hour)
                    else:
                        # Zeitlücke > 1h: Delta verwerfen (Kalibrierung).
                        logger.info(f"⏭️ Sensor {key}: Zeitlücke {time_diff}s — Delta {scaled_delta} verworfen.")

            self._save()

        return True

    # =========================================================
    # CSV TRACE (Verifikation)
    # =========================================================
    def _trace_csv(self, sensor_id: str, ts: int, current: float, last: float, raw_delta: float, scaled_delta: float, hour: int):
        """Schreibt eine Zeile in logs/trace_deltas.csv für Nachvollziehbarkeit."""
        try:
            from app.core.app_config import settings
            trace_file = settings.LOG_DIR / "trace_deltas.csv"
            trace_file.parent.mkdir(parents=True, exist_ok=True)

            # Header schreiben wenn Datei neu
            write_header = not trace_file.exists()

            with open(trace_file, "a", encoding="utf-8") as f:
                if write_header:
                    f.write("timestamp,sensor_id,current,last,raw_delta,scale_factor,scaled_delta,hour\n")
                f.write(f"{ts},{sensor_id},{current},{last},{raw_delta},{self.scale_factor},{scaled_delta},{hour}\n")
        except Exception:
            pass  # Trace darf nie die App crashen

    # =========================================================
    # READ ACCESS
    # =========================================================
    def get_all(self) -> dict[str, SensorStateEntry]:
        return self.data

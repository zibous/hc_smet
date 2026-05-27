import time
import yaml
import os
import sys
from pathlib import Path
import logging
import sqlite3
from datetime import datetime

from sensor import S0Sensor
from storage import StorageHandler
from network import NetworkClient
from pokeydevice import PoKeysDevice

# Projektwurzel ermitteln
ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT))

from app.core.app_config import settings
logger = logging.getLogger(__name__)


# --- SQLite Hilfsklasse für stündliche Werte (Optimierte Batch-Version) ---
class DatabaseHandler:
    def __init__(self, db_path="sensordata.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path, timeout=30.0) as conn:
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("PRAGMA synchronous=NORMAL;")
            conn.execute("""
            CREATE TABLE IF NOT EXISTS hourly_values (
                sensor_id TEXT NOT NULL,
                hour INTEGER NOT NULL,
                consumption REAL NOT NULL,
                total REAL,
                PRIMARY KEY (sensor_id, hour)
            )
            """)
            conn.commit()

    def write_hourly_batch(self, batch_data):
        """
        Schreibt eine Liste von Sensordaten in einer einzigen Transaktion.
        batch_data muss eine Liste von Tupeln sein: [(sensor_id, consumption, total_kwh), ...]
        """
        if not batch_data:
            return

        now = datetime.now()
        hour_ts = int(now.replace(minute=0, second=0, microsecond=0).timestamp())

        # Daten für das SQL-Statement aufbereiten und Spitzenschutz anwenden
        sql_rows = []
        for sensor_id, consumption, total_kwh in batch_data:
            if consumption < 0 or consumption > 50.0:
                logger.warning(f"[DB-SCHUTZ] Absurde Spitze blockiert für {sensor_id}: {consumption} kWh")
                continue
            sql_rows.append((sensor_id, hour_ts, consumption, total_kwh))

        if not sql_rows:
            return

        # Alle Einträge in einer einzigen atomaren Transaktion schreiben
        with sqlite3.connect(self.db_path, timeout=30.0) as conn:
            conn.executemany("""
                INSERT INTO hourly_values (sensor_id, hour, consumption, total)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(sensor_id, hour) DO UPDATE SET
                    consumption = excluded.consumption,
                    total = excluded.total
            """, sql_rows)
            conn.commit()

    def get_latest_total_from_db(self, sensor_id: str) -> float | None:
        try:
            with sqlite3.connect(self.db_path, timeout=30.0) as conn:
                cursor = conn.execute("""
                    SELECT total FROM hourly_values
                    WHERE sensor_id = ?
                    ORDER BY hour DESC LIMIT 1
                """, (sensor_id,))
                row = cursor.fetchone()
                return float(row[0]) if row and row[0] is not None else None
        except Exception as e:
            logger.error(f"[DB-ERROR] Fehler beim Lesen des letzten Standes für {sensor_id}: {e}")
            return None

    def get_current_hour_data(self, sensor_id: str) -> tuple[float, float] | None:
        now = datetime.now()
        hour_ts = int(now.replace(minute=0, second=0, microsecond=0).timestamp())
        try:
            with sqlite3.connect(self.db_path, timeout=30.0) as conn:
                cursor = conn.execute("""
                    SELECT consumption, total FROM hourly_values
                    WHERE sensor_id = ? AND hour = ?
                """, (sensor_id, hour_ts))
                row = cursor.fetchone()
                if row and row[0] is not None and row[1] is not None:
                    return float(row[0]), float(row[1])
            return None
        except Exception as e:
            logger.error(f"[DB-ERROR] Fehler beim Lesen der aktuellen Stunde für {sensor_id}: {e}")
            return None


def parse_range(text: str) -> tuple[int, int]:
    start, end = map(int, text.split("-"))
    return start, end

class PoKeysManager:

    def __init__(self):

        self.settings = settings
        self.devices = []   # ← WICHTIG: immer definieren!
        self._load_devices()
        self.network = NetworkClient()

        filename = os.path.splitext(os.path.basename(__file__))[0] + ".json"
        self.storage = StorageHandler(filename)

        # Datenbank & Stunden-Cache initialisieren
        self.db = DatabaseHandler("sensordata.db")
        self.db_hour_start_cache = {}

        # Stundenwechsel beim Start korrekt erkennen
        self.last_processed_hour = None

        self.sensors = {}
        self.letztes_update = "Noch keine Daten empfangen"

        # ---------------- YAML laden ----------------
        with open("house.yaml", encoding="utf-8") as f:
            cfg = yaml.safe_load(f)

        sensor_cfg = cfg["sensors"]

        # ---------------- Sensoren erzeugen ----------------
        for sid, data in sensor_cfg.items():
            sensor = S0Sensor(data["name"], data["impulse"])
            sensor.model = data["model"]
            sensor.id = sid
            sensor.room = data.get("room")
            sensor.devices = data.get("devices", [])

            # NEU: Flag für „hat jemals Impulse gehabt?“
            sensor.has_ever_pulsed = False

            self.sensors[sid] = sensor

        # ---------------- Interfaces zuordnen ----------------
        for sid, sensor in self.sensors.items():
            num = int(sid[1:])
            for dev in self.devices:
                if dev.start_id <= num <= dev.end_id:
                    dev.sensors.append(sid)
                    sensor.interface = dev.id
                    break

        # ---------------- Pins zuordnen ----------------
        self.pin_order = [
            int(pin.strip())
            for pin in settings.POKEYS_DEVICE2_PINS.split(",")
        ]

        for dev in self.devices:
            dev.sensors.sort()
            for index, sid in enumerate(dev.sensors):
                if index < len(self.pin_order):
                    self.sensors[sid].pin = self.pin_order[index]

        # ---------------- 1. Persistente Daten aus JSON laden ----------------
        self.storage.load(self.sensors)

        # ---------------- 2. CROSS-CHECK JSON vs SQLITE ----------------
        for sid, sensor in self.sensors.items():
            try:
                current_hour_db = self.db.get_current_hour_data(sid)
                latest_db_total = self.db.get_latest_total_from_db(sid)

                # NEU: Automatische Erkennung, ob Sensor jemals Impulse hatte
                if sensor.total_kwh > 0:
                    sensor.has_ever_pulsed = True
                if latest_db_total is not None and latest_db_total > 0:
                    sensor.has_ever_pulsed = True

                json_valid = sensor.initialized and sensor.total_kwh >= 0

                # ---------------- FALL A: JSON gültig ----------------
                if json_valid:
                    if current_hour_db:
                        db_consumption, db_total = current_hour_db
                        self.db_hour_start_cache[sid] = round(sensor.total_kwh - db_consumption, 6)
                        logger.info(f"[{sid}] Stunden-Cache aus SQLite rekonstruiert (Verbrauch bisher: {db_consumption} kWh).")
                    else:
                        self.db_hour_start_cache[sid] = sensor.total_kwh
                    continue

                # ---------------- FALL B: SQLite hat Daten ----------------
                if latest_db_total is not None:
                    sensor.total_kwh = latest_db_total
                    sensor.prev_kwh = latest_db_total
                    sensor.verbrauch_kwh = 0.0
                    sensor.initialized = True

                    logger.info(f"[{sid}] Historische Daten aus SQLite geladen: {latest_db_total} kWh")

                    if current_hour_db:
                        db_consumption, db_total = current_hour_db
                        self.db_hour_start_cache[sid] = round(latest_db_total - db_consumption, 6)
                    else:
                        self.db_hour_start_cache[sid] = latest_db_total

                    continue

                # ---------------- FALL C: echter Kaltstart ----------------
                if not sensor.has_ever_pulsed:
                    self.db_hour_start_cache[sid] = sensor.total_kwh
                    logger.critical(f"[{sid}] Keine historischen Daten in JSON oder SQLite gefunden (Kaltstart).")
                else:
                    # Sensor hat schon existiert, aber keine Daten gespeichert → kein Fehler
                    self.db_hour_start_cache[sid] = sensor.total_kwh
                    logger.info(f"[{sid}] Sensor hat noch nie Verbrauch gehabt – kein Kaltstart.")

            except Exception as e:
                logger.error(f"Fehler beim Cross-Check für Sensor {sid}: {e}")
                self.db_hour_start_cache[sid] = sensor.total_kwh



    def _load_devices(self):
        idx = 1
        while hasattr(self.settings, f"POKEYS_DEVICE{idx}_NAME"):
            name = getattr(self.settings, f"POKEYS_DEVICE{idx}_NAME")
            ip   = getattr(self.settings, f"POKEYS_DEVICE{idx}_IP")
            rng  = getattr(self.settings, f"POKEYS_DEVICE{idx}_SENSORS")
            start, end = map(int, rng.split("-"))
            logger.info(f"Device {name}, {ip} ready")
            self.devices.append(
                PoKeysDevice(name, ip, start, end)
            )
            idx += 1

    def update_sensors(self):
        self.letztes_update = time.strftime("%Y-%m-%d %H:%M:%S")

        current_hour = datetime.now().hour
        is_new_hour = (self.last_processed_hour is not None and current_hour != self.last_processed_hour)

        db_batch = []

        for dev in self.devices:
            try:
                result = self.network.fetch(dev.ip)
                logger.info(f"Loaded device data von: {dev.ip}, Ergebnisse neu geladen.")
            except Exception:
                dev.mark_offline()
                for sid in dev.sensors:
                    self.sensors[sid].online = False
                continue

            if not result.get("online", False):
                dev.mark_offline()
                for sid in dev.sensors:
                    self.sensors[sid].online = False
                continue

            dev.mark_online()
            data = result.get("data", {})

            for s in data.get("sensors", []):
                sid = s.get("ID")
                val = s.get("Val")
                if sid not in self.sensors:
                    continue

                sensor = self.sensors[sid]
                sensor.online = True
                sensor.last_online_ts = time.time()

                try:
                    # Stunden-Cache neu setzen
                    if sid not in self.db_hour_start_cache or is_new_hour:
                        self.db_hour_start_cache[sid] = sensor.total_kwh

                    # Update
                    sensor.update(float(val))

                    # NEU: Wenn total_kwh > 0 → Sensor hat Impulse
                    if sensor.total_kwh > 0:
                        sensor.has_ever_pulsed = True

                    consumption = round(sensor.total_kwh - self.db_hour_start_cache[sid], 6)

                    if consumption < 0:
                        consumption = 0.0
                        self.db_hour_start_cache[sid] = sensor.total_kwh

                    # NEU: Nur speichern, wenn sinnvoll
                    if consumption > 0.0 or sensor.total_kwh > 0.0:
                        db_batch.append((sid, consumption, sensor.total_kwh))
                    else:
                        logger.debug(f"[{sid}] Kein Verbrauch & total=0.0 → nicht in DB gespeichert.")

                    logger.info(f" Speichere Werte für ID: {sid}, Verbrauch:{consumption} kwh: {sensor.total_kwh}")

                except Exception:
                    logger.error(f"Fehler beim Update des Sensors {sid}")
                    continue

        try:
            self.db.write_hourly_batch(db_batch)
        except Exception as e:
            logger.error(f"Fehler beim Schreiben des Datenbank-Batches: {e}")

        self.storage.save(self.sensors)

        self.last_processed_hour = current_hour

    # ----------------------------------------------------------------------

    def get_all_data(self):
        now = time.time()
        out = {}

        for sid, s in self.sensors.items():
            d = s.to_dict()
            if d["online"]:
                d["status"] = "OK"
            else:
                offline_secs = int(now - d.get("last_online_ts", now))
                d["status"] = f"OFF {offline_secs}s"
            out[sid] = d

        return out

    def get_single_value(self, sid: str):
        return self.sensors.get(sid.upper())

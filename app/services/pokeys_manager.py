# -*- coding: utf-8 -*-
"""PoKeysManager — Zentrale Steuerung der GET-basierten Datenbeschaffung.

Orchestriert:
- YAML-Konfiguration laden (aus settings.mapping_file)
- Sensor-Objekte erzeugen und Interfaces zuordnen
- Pin-Mapping
- Periodisches Polling via NetworkClient
- Stündliche DB-Batch-Writes
- JSON-Persistenz (StorageHandler)
- Cross-Check JSON vs. SQLite beim Start

100% SCHUTZ VOR APPAUSFALL-HOCHSCHIESSEN durch:
1. S0Sensor.update() — Zähler-Reset + Spike-Schutz
2. DatabaseHandler — Absurde Spitzen blockiert (>50 kWh/h)
3. Cross-Check beim Start — Bester Wert aus JSON/SQLite gewinnt
"""

import logging
import threading
import time
from datetime import datetime

import yaml

from app.core.app_config import settings
from app.domain.pokey_device import PoKeysDevice
from app.domain.s0_sensor import S0Sensor
from app.infrastructure.database.dbconnect import Database
from app.infrastructure.network_client import NetworkClient
from app.services.state.storage_handler import StorageHandler

logger = logging.getLogger(__name__)


class PoKeysManager:
    """Zentrale Steuerung für GET-basierte PoKeys-Datenbeschaffung."""

    def __init__(self):
        self.devices: list[PoKeysDevice] = []
        self.sensors: dict[str, S0Sensor] = {}
        self.network = NetworkClient()
        self.letztes_update = "Noch keine Daten empfangen"

        # Stunden-Cache für DB-Writes
        self.db_hour_start_cache: dict[str, float] = {}
        self.last_processed_hour: int | None = None

        # Devices aus Settings laden
        self._load_devices()

        # Storage-Pfad aus Settings
        storage_path = settings.DATA_DIR / "pokeys_state.json"
        self.storage = StorageHandler(storage_path)

        # YAML-Konfiguration laden und Sensoren erzeugen
        self._load_sensors_from_yaml()

        # Interfaces und Pins zuordnen
        self._assign_interfaces()
        self._assign_pins()

        # 1. Persistente Daten aus JSON laden
        self.storage.load(self.sensors)

        # 2. Cross-Check JSON vs. SQLite
        self._cross_check_startup()

        # 3. Prognosen aus Analytics-DB laden
        self._load_prognosis()

        logger.info(
            f"✅ PoKeysManager initialisiert: "
            f"{len(self.devices)} Devices, {len(self.sensors)} Sensoren"
        )

    # ==================================================================
    # INITIALISIERUNG
    # ==================================================================

    def _load_devices(self):
        """Lädt Device-Konfiguration aus app_config settings."""
        idx = 1
        while hasattr(settings, f"POKEYS_DEVICE{idx}_NAME"):
            name = getattr(settings, f"POKEYS_DEVICE{idx}_NAME")
            ip = getattr(settings, f"POKEYS_DEVICE{idx}_IP")
            rng = getattr(settings, f"POKEYS_DEVICE{idx}_SENSORS")
            start, end = map(int, rng.split("-"))
            self.devices.append(PoKeysDevice(name, ip, start, end))
            logger.info(f"Device {name} ({ip}) registriert: Sensoren {start}-{end}")
            idx += 1

    def _load_sensors_from_yaml(self):
        """Lädt Sensor-Definitionen aus house.yaml (Pfad aus settings)."""
        yaml_path = settings.mapping_file

        if not yaml_path.exists():
            raise FileNotFoundError(
                f"Kritisch: house.yaml nicht gefunden unter {yaml_path}"
            )

        with open(yaml_path, encoding="utf-8") as f:
            cfg = yaml.safe_load(f)

        sensor_cfg = cfg.get("sensors", {})

        for sid, data in sensor_cfg.items():
            sensor = S0Sensor(data["name"], data["impulse"])
            sensor.model = data.get("model")
            sensor.id = sid
            sensor.room = data.get("room")
            sensor.devices = data.get("devices", [])
            sensor.has_ever_pulsed = False
            self.sensors[sid] = sensor

    def _assign_interfaces(self):
        """Ordnet Sensoren automatisch den PoKeys-Interfaces zu."""
        for sid, sensor in self.sensors.items():
            num = int(sid[1:])
            for dev in self.devices:
                if dev.start_id <= num <= dev.end_id:
                    dev.sensors.append(sid)
                    sensor.interface = dev.id
                    break

    def _assign_pins(self):
        """Weist Sensoren ihre Hardware-Pins zu (aus settings)."""
        pin_order = [
            int(pin.strip())
            for pin in settings.POKEYS_DEVICE1_PINS.split(",")
        ]

        for dev in self.devices:
            dev.sensors.sort()
            for index, sid in enumerate(dev.sensors):
                if index < len(pin_order):
                    self.sensors[sid].pin = pin_order[index]

    def _cross_check_startup(self):
        """Cross-Check JSON vs. SQLite beim Start — Crash-Recovery."""
        if Database._instance is None:
            # DB noch nicht initialisiert → nur JSON verwenden
            for sid in self.sensors:
                self.db_hour_start_cache[sid] = self.sensors[sid].total_kwh
            return

        for sid, sensor in self.sensors.items():
            try:
                current_hour_db = self._get_current_hour_data(sid)
                latest_db_total = self._get_latest_total_from_db(sid)

                # Automatische Erkennung ob Sensor jemals Impulse hatte
                if sensor.total_kwh > 0:
                    sensor.has_ever_pulsed = True
                if latest_db_total is not None and latest_db_total > 0:
                    sensor.has_ever_pulsed = True

                json_valid = sensor.initialized and sensor.total_kwh >= 0

                # FALL A: JSON gültig
                if json_valid:
                    if current_hour_db:
                        db_consumption, _ = current_hour_db
                        self.db_hour_start_cache[sid] = round(
                            sensor.total_kwh - db_consumption, 6
                        )
                        logger.info(
                            f"[{sid}] Stunden-Cache aus SQLite rekonstruiert "
                            f"(Verbrauch bisher: {db_consumption} kWh)."
                        )
                    else:
                        self.db_hour_start_cache[sid] = sensor.total_kwh
                    continue

                # FALL B: SQLite hat Daten
                if latest_db_total is not None:
                    sensor.total_kwh = latest_db_total
                    sensor.prev_kwh = latest_db_total
                    sensor.verbrauch_kwh = 0.0
                    sensor.initialized = True
                    logger.info(
                        f"[{sid}] Historische Daten aus SQLite geladen: "
                        f"{latest_db_total} kWh"
                    )

                    if current_hour_db:
                        db_consumption, _ = current_hour_db
                        self.db_hour_start_cache[sid] = round(
                            latest_db_total - db_consumption, 6
                        )
                    else:
                        self.db_hour_start_cache[sid] = latest_db_total
                    continue

                # FALL C: Kaltstart
                self.db_hour_start_cache[sid] = sensor.total_kwh
                if not sensor.has_ever_pulsed:
                    logger.info(
                        f"[{sid}] Kaltstart — keine historischen Daten."
                    )
                else:
                    logger.info(
                        f"[{sid}] Sensor ohne Last — kein Fehler."
                    )

            except Exception as e:
                logger.error(f"Fehler beim Cross-Check für {sid}: {e}")
                self.db_hour_start_cache[sid] = sensor.total_kwh

    # ==================================================================
    # UPDATE LOOP — Kernlogik
    # ==================================================================

    def _load_prognosis(self):
        """Lädt Prognose-Werte aus der Analytics-DB (sensor_prognosis).

        Wird beim Start aufgerufen. Falls die Tabelle nicht existiert
        oder leer ist, werden keine Prognosen geladen (Fallback greift).
        """
        try:
            analytics_path = settings.analytics_db_path
            if not analytics_path.exists():
                logger.info("Analytics-DB nicht gefunden — Prognosen werden live berechnet.")
                return

            import sqlite3
            conn = sqlite3.connect(str(analytics_path))
            conn.row_factory = sqlite3.Row

            try:
                rows = conn.execute("SELECT * FROM sensor_prognosis").fetchall()
            except Exception:
                logger.info("Tabelle sensor_prognosis nicht vorhanden — übersprungen.")
                conn.close()
                return

            loaded = 0
            for row in rows:
                sid = row["sensor_id"]
                if sid in self.sensors:
                    self.sensors[sid].load_prognosis(dict(row))
                    loaded += 1

            conn.close()

            if loaded > 0:
                logger.info(f"✅ Prognosen für {loaded} Sensoren aus Analytics-DB geladen.")
            else:
                logger.info("Keine Prognosen in Analytics-DB gefunden.")

        except Exception as e:
            logger.warning(f"⚠️ Fehler beim Laden der Prognosen: {e}")

    def update_sensors(self):
        """Holt Daten von allen PoKeys-Interfaces und aktualisiert Sensoren.

        Wird periodisch vom Polling-Thread aufgerufen.
        """
        self.letztes_update = time.strftime("%Y-%m-%d %H:%M:%S")

        current_hour = datetime.now().hour
        is_new_hour = (
            self.last_processed_hour is not None
            and current_hour != self.last_processed_hour
        )

        db_batch: list[tuple[str, float, float]] = []

        for dev in self.devices:
            try:
                result = self.network.fetch(dev.ip)
            except Exception as e:
                logger.error(f"Netzwerkfehler für {dev.ip}: {e}")
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
                    # Stunden-Cache neu setzen bei Stundenwechsel
                    if sid not in self.db_hour_start_cache or is_new_hour:
                        self.db_hour_start_cache[sid] = sensor.total_kwh

                    # Sensor-Update (mit Spike-Schutz)
                    sensor.update(float(val))

                    # Flag aktualisieren
                    if sensor.total_kwh > 0:
                        sensor.has_ever_pulsed = True

                    # Stündlichen Verbrauch berechnen
                    consumption = round(
                        sensor.total_kwh - self.db_hour_start_cache[sid], 6
                    )

                    if consumption < 0:
                        consumption = 0.0
                        self.db_hour_start_cache[sid] = sensor.total_kwh

                    # Nur sinnvolle Werte in DB-Batch aufnehmen
                    if consumption > 0.0 or sensor.total_kwh > 0.0:
                        db_batch.append((sid, consumption, sensor.total_kwh))

                except Exception as e:
                    logger.error(f"Fehler beim Update von Sensor {sid}: {e}")
                    continue

        # DB-Batch schreiben
        self._write_hourly_batch(db_batch)

        # JSON-Persistenz speichern
        self.storage.save(self.sensors)

        self.last_processed_hour = current_hour

    # ==================================================================
    # DATENBANK — Stündliche Werte
    # ==================================================================

    def _write_hourly_batch(self, batch_data: list[tuple[str, float, float]]):
        """Schreibt Stundenwerte als Batch in die SQLite-DB.

        SCHUTZ: Absurde Spitzen (>50 kWh/h oder <0) werden blockiert.
        Timestamps werden in UTC gespeichert (konsistent mit POST-Modus).
        """
        if not batch_data or Database._instance is None:
            return

        import time as _time
        now_ts = int(_time.time())
        hour_ts = (now_ts // 3600) * 3600  # UTC-basiert, wie POST-Modus
        year = datetime.utcfromtimestamp(hour_ts).year

        # Spitzenschutz anwenden
        sql_rows = []
        for sensor_id, consumption, total_kwh in batch_data:
            if consumption < 0 or consumption > 50.0:
                logger.warning(
                    f"[DB-SCHUTZ] Absurde Spitze blockiert für "
                    f"{sensor_id}: {consumption} kWh"
                )
                continue
            sql_rows.append((sensor_id, hour_ts, consumption, total_kwh))

        if not sql_rows:
            return

        try:
            conn = Database._instance.get_conn(year=year)

            # Tabelle sicherstellen
            conn.execute("""
                CREATE TABLE IF NOT EXISTS hourly_values (
                    sensor_id TEXT NOT NULL,
                    hour INTEGER NOT NULL,
                    consumption REAL NOT NULL,
                    total REAL,
                    PRIMARY KEY (sensor_id, hour)
                )
            """)
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_hour ON hourly_values(hour)"
            )

            conn.executemany("""
                INSERT INTO hourly_values (sensor_id, hour, consumption, total)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(sensor_id, hour) DO UPDATE SET
                    consumption = excluded.consumption,
                    total = excluded.total
            """, sql_rows)
            conn.commit()
            conn.close()

        except Exception as e:
            logger.error(f"❌ Fehler beim DB-Batch-Write: {e}")

    def _get_latest_total_from_db(self, sensor_id: str) -> float | None:
        """Holt den letzten bekannten total_kwh aus der DB."""
        if Database._instance is None:
            return None
        try:
            conn = Database._instance.get_conn()
            cursor = conn.execute("""
                SELECT total FROM hourly_values
                WHERE sensor_id = ?
                ORDER BY hour DESC LIMIT 1
            """, (sensor_id,))
            row = cursor.fetchone()
            conn.close()
            return float(row[0]) if row and row[0] is not None else None
        except Exception as e:
            logger.error(f"[DB-ERROR] Lesen des letzten Standes für {sensor_id}: {e}")
            return None

    def _get_current_hour_data(
        self, sensor_id: str
    ) -> tuple[float, float] | None:
        """Holt consumption und total der aktuellen Stunde aus der DB."""
        if Database._instance is None:
            return None
        import time as _time
        now_ts = int(_time.time())
        hour_ts = (now_ts // 3600) * 3600  # UTC-basiert
        try:
            conn = Database._instance.get_conn()
            cursor = conn.execute("""
                SELECT consumption, total FROM hourly_values
                WHERE sensor_id = ? AND hour = ?
            """, (sensor_id, hour_ts))
            row = cursor.fetchone()
            conn.close()
            if row and row[0] is not None and row[1] is not None:
                return float(row[0]), float(row[1])
            return None
        except Exception as e:
            logger.error(
                f"[DB-ERROR] Lesen der aktuellen Stunde für {sensor_id}: {e}"
            )
            return None

    # ==================================================================
    # READ ACCESS — Für Dashboard, MQTT, API
    # ==================================================================

    def get_all_data(self) -> dict[str, dict]:
        """Liefert alle Sensordaten als Dictionary für UI/API.

        Returns:
            {
                "S01": {
                    "name": "Licht",
                    "watt": 59,
                    "total_kwh": 95.584,
                    "verbrauch_kwh": 0.001,
                    "kosten": 0.024,
                    "co2": 38.0,
                    "prognose_tag": 1.2,
                    "prognose_jahr": 438.0,
                    "energieklasse": "G",
                    "model": "eacWSZ-50A",
                    "devices": ["pumpe", "licht"],
                    "room": "EG_R02",
                    "pin": 0,
                    "interface": "poKey64",
                    "online": True,
                    "status": "OK",
                    ...
                }
            }
        """
        now = time.time()
        out = {}

        for sid, s in self.sensors.items():
            d = s.to_dict()
            # Zusätzliche Metadaten
            d["name"] = s.name
            d["model"] = s.model
            d["room"] = s.room
            d["devices"] = s.devices
            d["pin"] = s.pin
            d["interface"] = s.interface
            d["faktor"] = s.faktor

            # Status-Berechnung
            if d["online"]:
                d["status"] = "OK"
            else:
                offline_secs = int(now - d.get("last_online_ts", now))
                d["status"] = f"OFF {offline_secs}s"

            out[sid] = d

        return out

    def get_single_sensor(self, sid: str) -> S0Sensor | None:
        """Holt einen einzelnen Sensor nach ID."""
        return self.sensors.get(sid.upper())


# ======================================================================
# POLLING THREAD
# ======================================================================

def start_polling_thread(
    manager: PoKeysManager, interval: int
) -> threading.Event:
    """Startet den Polling-Thread für periodische Datenbeschaffung.

    Args:
        manager: PoKeysManager-Instanz
        interval: Polling-Intervall in Sekunden

    Returns:
        threading.Event zum Stoppen des Threads
    """
    stop_event = threading.Event()

    def _poll_loop():
        logger.info(
            f"🔄 Polling-Thread gestartet (Intervall: {interval}s)"
        )
        # Erster Durchlauf: Basiswerte initialisieren
        try:
            manager.update_sensors()
        except Exception as e:
            logger.error(f"Fehler beim initialen Sensor-Update: {e}")

        while not stop_event.is_set():
            stop_event.wait(timeout=interval)
            if not stop_event.is_set():
                try:
                    manager.update_sensors()
                except Exception as e:
                    # WICHTIG: App darf NICHT crashen!
                    logger.error(
                        f"Polling-Fehler (App läuft weiter): {e}"
                    )

        logger.info("🛑 Polling-Thread gestoppt.")

    thread = threading.Thread(
        target=_poll_loop, daemon=True, name="pokeys-poller"
    )
    thread.start()
    return stop_event

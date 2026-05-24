#!/usr/bin/env python3

import os
import sqlite3
import statistics
import time
import logging
import requests
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from dotenv import load_dotenv
from apscheduler.schedulers.blocking import BlockingScheduler

load_dotenv()

# =========================================================
# SETTINGS & PATHS
# =========================================================
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / os.getenv("DATA_DIR", "data")

ANALYTICS_DB_PATH_ENV = os.getenv("ANALYTICS_DB_PATH")
if ANALYTICS_DB_PATH_ENV:
    ANALYTICS_DB = Path(BASE_DIR / ANALYTICS_DB_PATH_ENV).resolve()
else:
    ANALYTICS_DB = Path(DATA_DIR / "analytics.sqlite").resolve()

# Name der zu ignorierenden Datenbanken aus der .env laden
IGNORE_DBS_ENV = os.getenv("IGNORE_DBS", "analytics.sqlite")
IGNORE_DB_LIST = [name.strip() for name in IGNORE_DBS_ENV.split(",") if name.strip()]

DATA_DIR.mkdir(parents=True, exist_ok=True)
ANALYTICS_DB.parent.mkdir(parents=True, exist_ok=True)

# =========================================================
# 📝 LOGGING SETUP
# =========================================================
LOG_FILE = DATA_DIR / "analytics.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("energy_analytics")

YEAR_FROM = int(os.getenv("YEAR_FROM", "1970"))
YEAR_TO = int(os.getenv("YEAR_TO", "2100"))

# =========================================================
# CLUSTER CLASSIFICATION (konfigurierbar via .env)
# Format: "schwelle:label,schwelle:label,schwelle:label"
# Absteigend sortiert — erster Treffer gewinnt.
# =========================================================
def _parse_cluster_thresholds() -> list[tuple[float, str]]:
    raw = os.getenv("CLUSTER_THRESHOLDS", "30:Hoch,12:Mittel,0:Niedrig")
    thresholds = []
    for entry in raw.split(","):
        entry = entry.strip()
        if ":" in entry:
            val, label = entry.split(":", 1)
            thresholds.append((float(val.strip()), label.strip()))
    # Absteigend sortieren
    thresholds.sort(key=lambda x: x[0], reverse=True)
    return thresholds

CLUSTER_THRESHOLDS = _parse_cluster_thresholds()

def classify_peak(peak_pct: float) -> str:
    """Klassifiziert den Peak-Anteil anhand der konfigurierten Schwellenwerte."""
    for threshold, label in CLUSTER_THRESHOLDS:
        if peak_pct > threshold:
            return label
    # Fallback: letztes Label oder "Unbekannt"
    return CLUSTER_THRESHOLDS[-1][1] if CLUSTER_THRESHOLDS else "Unbekannt"

# =========================================================
# 🔗 WEBHOOK NOTIFICATION CLASS
# =========================================================
class Webhook:
    def __init__(self, base_url: str, webhook_id: str, timeout: int = 5):
        self.base_url = base_url.rstrip("/")
        self.webhook_id = webhook_id
        self.timeout = timeout

    @property
    def url(self) -> str:
        return f"{self.base_url}/api/webhook/{self.webhook_id}"

    def send(self, data: Optional[Dict[str, Any]] = None) -> bool:
        try:
            response = requests.post(self.url, json=data or {}, timeout=self.timeout)
            response.raise_for_status()
            return True
        except requests.RequestException as e:
            logger.error(f"❌ Webhook send failed: {e}")
            return False

_webhook: Optional[Webhook] = None

def _get_webhook() -> Optional[Webhook]:
    global _webhook
    if _webhook is not None: return _webhook
    url = os.getenv("HA_WEBHOOK_URL")
    wid = os.getenv("HA_WEBHOOK_ID")
    if url and wid:
        _webhook = Webhook(base_url=url, webhook_id=wid)
        return _webhook
    return None

def notify_ha(event: str, **kwargs) -> bool:
    wh = _get_webhook()
    if not wh: return False
    try:
        payload: Dict[str, Any] = {
            "event": event,
            "application": "hc_smet_analytics",
            "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        }
        payload.update(kwargs)
        ok = wh.send(payload)
        if ok: logger.info(f"🔔 Webhook erfolgreich abgesetzt: {event}")
        return ok
    except Exception as e:
        logger.error(f"⚠️ Webhook-Fehler: {e}")
        return False

# =========================================================
# DATABASES & PARSERS
# =========================================================
def get_databases():
    return list(DATA_DIR.glob("*.sqlite")) + list(DATA_DIR.glob("*.db"))

def extract_year(ts):
    if ts is None: return None
    try:
        val = int(ts)
        if val > 100000000:
            return datetime.fromtimestamp(val, tz=timezone.utc).year
        else:
            return datetime.fromtimestamp(val * 3600, tz=timezone.utc).year
    except: pass
    try: return datetime.fromisoformat(str(ts)).year
    except: pass
    try: return int(str(ts)[:4])
    except: return None

def get_utc_datetime(ts):
    try:
        val = int(ts)
        return datetime.fromtimestamp(val if val > 100000000 else val * 3600, tz=timezone.utc)
    except: return None

# =========================================================
# ⚡ DELTA-STREAMING
# =========================================================
def stream_hourly_values(target_year=None):
    if target_year:
        databases = list(DATA_DIR.glob(f"*{target_year}*.db")) + list(DATA_DIR.glob(f"*{target_year}*.sqlite"))
        logger.info(f"📂 Delta-Modus: Filter auf Kalenderjahr {target_year} angewendet.")
    else:
        databases = list(DATA_DIR.glob("*.sqlite")) + list(DATA_DIR.glob("*.db"))
        logger.info("📂 Vollaufbau-Modus: Scanne alle historischen Datenbanken.")

    databases = [d for d in databases if d.name not in IGNORE_DB_LIST and d.resolve() != ANALYTICS_DB]
    logger.info(f"🔍 {len(databases)} gültige Quelldatenbank(en) im Verzeichnis gefunden.")

    for db in databases:
        logger.info(f"📖 Verarbeite Quelldatei: {db.name}")
        conn = sqlite3.connect(db)
        cur = conn.cursor()
        try:
            cur.execute("SELECT sensor_id, consumption, hour FROM hourly_values")
        except Exception:
            logger.warning(f"⚠️ Tabelle 'hourly_values' in {db.name} ist inkompatibel. Datei übersprungen.")
            conn.close()
            continue

        while True:
            chunk = cur.fetchmany(5000)
            if not chunk: break
            for sensor, value, ts in chunk:
                if sensor is None or value is None: continue
                try: value = float(value)
                except: continue
                yield (sensor, value, ts)
        conn.close()

# =========================================================
# SQLITE INIT (Zieldatenbank-Strukturen komplettiert)
# =========================================================
def init_database():
    conn = sqlite3.connect(ANALYTICS_DB)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS yearly_report (
            year INTEGER PRIMARY KEY, entries INTEGER, total REAL, avg_month REAL, avg_day REAL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS sensor_monthly (
            sensor_id TEXT, year INTEGER, month INTEGER, total_consumption REAL, PRIMARY KEY (sensor_id, year, month)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS sensor_clusters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_timestamp TEXT,
            sensor_id TEXT,
            cluster TEXT,
            total REAL,
            base REAL,
            mid REAL,
            peak REAL,
            samples INTEGER,
            peak_percent REAL,
            average REAL,
            median REAL,
            minimum REAL,
            maximum REAL,
            stddev REAL,
            load_factor REAL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS sensor_daily (
            sensor_id TEXT, day TEXT, total REAL, average REAL, minimum_baseload REAL,
            maximum_peak REAL, load_factor REAL, samples INTEGER, is_complete INTEGER, PRIMARY KEY (sensor_id, day)
        )
    """)

    cur.execute("CREATE INDEX IF NOT EXISTS idx_sensor_month ON sensor_monthly(sensor_id, year)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_sensor ON sensor_clusters(sensor_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_cluster ON sensor_clusters(cluster)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_day ON sensor_daily(day)")

    conn.commit()
    conn.close()
    logger.info(f"✅ Analytics-Datenbank initialisiert ({ANALYTICS_DB.name})")

# =========================================================
# CLASSIFICATION & ENGINE
# =========================================================
def calculate_analytics(target_year=None):
    yearly, monthly_data, daily_data = {}, {}, {}
    sensor_all_values = {}

    for sensor, value, ts in stream_hourly_values(target_year):
        dt = get_utc_datetime(ts)
        if not dt: continue

        # 1. Globaler Jahresbericht
        year = dt.year
        if year not in yearly:
            yearly[year] = {'values': [], 'min_ts': None, 'max_ts': None}
        yearly[year]['values'].append(value)

        ts_seconds = int(dt.timestamp())
        if yearly[year]['min_ts'] is None:
            yearly[year]['min_ts'] = yearly[year]['max_ts'] = ts_seconds
        else:
            yearly[year]['min_ts'] = min(yearly[year]['min_ts'], ts_seconds)
            yearly[year]['max_ts'] = max(yearly[year]['max_ts'], ts_seconds)

        # 2. Sensor-Monatsdaten
        m_key = (sensor, dt.year, dt.month)
        monthly_data[m_key] = monthly_data.get(m_key, 0.0) + value
        y_key = (sensor, dt.year, 0)
        monthly_data[y_key] = monthly_data.get(y_key, 0.0) + value

        # 3. Sensor-Tagesdaten
        day_str = dt.strftime("%Y-%m-%d")
        d_key = (sensor, day_str)
        if d_key not in daily_data: daily_data[d_key] = []
        daily_data[d_key].append(value)

        # 4. Werte für Clustering puffern
        if sensor not in sensor_all_values:
            sensor_all_values[sensor] = []
        sensor_all_values[sensor].append(value)

    # Berechne Lastprofil-Cluster (sensor_clusters)
    sensor_clusters_rows = []
    run_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for sensor_id, raw_v in sensor_all_values.items():
        v_sorted = sorted([v for v in raw_v if v > 0])
        if not v_sorted: continue

        n = len(v_sorted)
        base_cut = max(1, int(n * 0.2))
        mid_cut = max(base_cut + 1, int(n * 0.9))

        base_sum = sum(v_sorted[:base_cut])
        mid_sum = sum(v_sorted[base_cut:mid_cut])
        peak_sum = sum(v_sorted[mid_cut:])
        total_sum = base_sum + mid_sum + peak_sum

        if total_sum == 0: continue

        peak_pct = (peak_sum / total_sum) * 100
        avg_val = statistics.mean(v_sorted)
        max_val = v_sorted[-1]

        cluster_name = classify_peak(peak_pct)

        # ✨ PRÄZISE RUNDUNG: Schutz der Cluster-Statistiken vor dem Schreiben
        sensor_clusters_rows.append((
            run_ts,
            sensor_id,
            cluster_name,
            round(total_sum, 2),
            round(base_sum, 2),
            round(mid_sum, 2),
            round(peak_sum, 2),
            n,
            round(peak_pct, 2),
            round(avg_val, 4),
            round(statistics.median(v_sorted), 4),
            round(v_sorted[0], 4),
            round(max_val, 4),
            round(statistics.stdev(v_sorted) if n > 1 else 0.0, 4),
            round(avg_val / max_val, 4) if max_val > 0 else 0.0
        ))

    return yearly, monthly_data, daily_data, sensor_clusters_rows

# =========================================================
# WRITE TRANSACTION
# =========================================================
def save_to_db(yearly, monthly_data, daily_data, sensor_clusters, target_year=None):
    conn = sqlite3.connect(ANALYTICS_DB)
    cur = conn.cursor()
    try:
        cur.execute("BEGIN TRANSACTION;")

        if target_year:
            cur.execute("DELETE FROM yearly_report WHERE year = ?;", (target_year,))
            cur.execute("DELETE FROM sensor_monthly WHERE year = ?;", (target_year,))
            cur.execute("DELETE FROM sensor_daily WHERE day LIKE ?;", (f"{target_year}-%",))
            if sensor_clusters:
                active_sensors = tuple(set(row[1] for row in sensor_clusters))
                if len(active_sensors) == 1:
                    cur.execute("DELETE FROM sensor_clusters WHERE sensor_id = ?;", active_sensors)
                else:
                    cur.execute(f"DELETE FROM sensor_clusters WHERE sensor_id IN {active_sensors};")
        else:
            cur.execute("DELETE FROM yearly_report;")
            cur.execute("DELETE FROM sensor_monthly;")
            cur.execute("DELETE FROM sensor_daily;")
            cur.execute("DELETE FROM sensor_clusters;")

        # ✨ PRÄZISE RUNDUNG: Bereinigung der Jahres-Durchschnitte aus den Quell-Ketten
        for year, data in yearly.items():
            values = data['values']
            total = sum(values)
            if data['min_ts'] and data['max_ts']:
                start_dt = datetime.fromtimestamp(data['min_ts'], tz=timezone.utc)
                end_dt = datetime.fromtimestamp(data['max_ts'], tz=timezone.utc)
                days = max(1, (end_dt.date() - start_dt.date()).days + 1)
                months = max(1, ((end_dt.year - start_dt.year) * 12 + (end_dt.month - start_dt.month) + 1))
                avg_day, avg_month = total / days, total / months
            else: avg_day = avg_month = 0
            cur.execute("INSERT INTO yearly_report VALUES (?, ?, ?, ?, ?);",
                        (year, len(values), round(total, 2), round(avg_month, 2), round(avg_day, 2)))

        # ✨ PRÄZISE RUNDUNG: Bereinigung der Monats-Daten
        for (sensor_id, year, month), total in monthly_data.items():
            cur.execute("INSERT INTO sensor_monthly VALUES (?, ?, ?, ?);", (sensor_id, year, month, round(total, 2)))

        # Inserts für Cluster-Analyse
        if sensor_clusters:
            cur.executemany("""
                INSERT INTO sensor_clusters (
                    run_timestamp, sensor_id, cluster, total, base, mid, peak,
                    samples, peak_percent, average, median, minimum, maximum, stddev, load_factor
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, sensor_clusters)

        # ✨ PRÄZISE RUNDUNG: Bereinigung der Tages-Statistiken
        for (sensor_id, day_str), values in daily_data.items():
            samples = len(values)
            day_total = sum(values)
            day_avg = statistics.mean(values)
            day_min = min(values)
            day_max = max(values)
            load_factor = round(day_avg / day_max, 4) if day_max > 0 else 0.0

            cur.execute("INSERT INTO sensor_daily VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);",
                        (sensor_id, day_str, round(day_total, 2), round(day_avg, 4), round(day_min, 2), round(day_max, 2), load_factor, samples, 1 if samples >= 24 else 0))

        conn.commit()
        logger.info("💾 Daten erfolgreich atomar in die Analytics-Datenbank weggeschrieben.")
    except Exception as e:
        conn.rollback()
        logger.error(f"❌ Transaktions-Fehler beim Speichern in SQLite: {e}")
        raise e
    finally:
        conn.close()

# =========================================================
# TRIGGER PIPELINE FUNCTION
# =========================================================
def run_pipeline():
    logger.info("Status: Processing Pipeline gestartet.")
    start_time = time.time()

    try:
        init_database()

        conn = sqlite3.connect(ANALYTICS_DB)
        row_count = conn.execute("SELECT COUNT(*) FROM yearly_report;").fetchone()
        conn.close()

        is_empty = (row_count[0] == 0) if row_count else True
        mode = "Vollaufbau" if is_empty else "Delta-Update"
        target_year = None if is_empty else datetime.now().year

        if is_empty:
            logger.info("📥 Initialer Vollaufbau getriggert. Scanne alle historischen Jahre...")
            yearly, monthly, daily, clusters = calculate_analytics(target_year=None)
            save_to_db(yearly, monthly, daily, clusters, target_year=None)
        else:
            logger.info(f"🔄 Inkrementelles Delta-Update für das aktuelle Jahr {target_year} gestartet...")
            yearly, monthly, daily, clusters = calculate_analytics(target_year=target_year)
            save_to_db(yearly, monthly, daily, clusters, target_year=target_year)

        duration = time.time() - start_time
        logger.info(f"🏁 Lauf erfolgreich beendet. Dauer: {duration:.2f} Sekunden.")

        notify_ha(
            event="pipeline_success",
            mode=mode,
            duration_seconds=round(duration, 2),
            processed_year=target_year or "All Years",
            daily_profiles=len(daily) if daily else 0
        )

    except Exception as e:
        logger.critical(f"💥 Kritischer Systemfehler während des Pipeline-Laufs: {e}", exc_info=True)
        notify_ha(
            event="pipeline_failed",
            error_message=str(e),
            severity="critical"
        )

if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("🚀 ENERGIE-ANALYTICS DAEMON GESTARTET")
    logger.info("=" * 60)

    run_pipeline()

    scheduler = BlockingScheduler()
    scheduler.add_job(run_pipeline, 'cron', hour=1, minute=15, timezone="Europe/Berlin")

    logger.info("⏰ Scheduler erfolgreich geladen. Wechsel in den Hintergrunddienst (01:15 Uhr täglich)...")
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("👋 Hintergrunddienst manuell beendet.")

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

    cur.execute("""
        CREATE TABLE IF NOT EXISTS sensor_prognosis (
            sensor_id TEXT PRIMARY KEY,
            avg_kwh_per_hour REAL,
            avg_kwh_per_day REAL,
            prognose_monat_eur REAL,
            prognose_jahr_eur REAL,
            prognose_jahr_kwh REAL,
            energieklasse TEXT,
            co2_jahr_kg REAL,
            trend_7d REAL,
            peak_hour INTEGER,
            base_load_w REAL,
            last_update TEXT
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
def calculate_prognosis():
    """Berechnet Prognose-Werte pro Sensor aus den letzten 30 Tagen hourly_values."""
    from datetime import timedelta

    logger.info("📊 Berechne Sensor-Prognosen aus historischen Daten...")

    # Strompreis und CO2 aus .env
    strompreis_raw = os.getenv("STROMPREISE", '{"2026":0.24}')
    try:
        import json as _json
        preise = _json.loads(strompreis_raw.strip("'"))
        strompreis = list(preise.values())[-1]
    except Exception:
        strompreis = 0.24

    co2_wert = float(os.getenv("CO2_WERT", "380"))  # g/kWh

    # Energieklassen-Grenzen
    limit_a = float(os.getenv("LIMIT_CLASS_A", "100"))
    limit_b = float(os.getenv("LIMIT_CLASS_B", "150"))
    limit_c = float(os.getenv("LIMIT_CLASS_C", "200"))
    limit_d = float(os.getenv("LIMIT_CLASS_D", "300"))
    limit_e = float(os.getenv("LIMIT_CLASS_E", "400"))
    limit_f = float(os.getenv("LIMIT_CLASS_F", "500"))

    now = datetime.now(timezone.utc)
    cutoff_30d = int((now - timedelta(days=30)).timestamp())
    cutoff_7d = int((now - timedelta(days=7)).timestamp())

    # Alle hourly_values der letzten 30 Tage laden
    sensor_hours_30d: dict[str, list[tuple[int, float]]] = {}
    sensor_hours_7d: dict[str, list[float]] = {}

    for sensor, value, ts in stream_hourly_values(target_year=now.year):
        try:
            ts_int = int(ts)
        except (TypeError, ValueError):
            continue

        if ts_int < cutoff_30d:
            continue

        if sensor not in sensor_hours_30d:
            sensor_hours_30d[sensor] = []
        sensor_hours_30d[sensor].append((ts_int, value))

        if ts_int >= cutoff_7d:
            if sensor not in sensor_hours_7d:
                sensor_hours_7d[sensor] = []
            sensor_hours_7d[sensor].append(value)

    # Pro Sensor Prognose berechnen
    prognosis_rows = []
    run_ts = now.strftime("%Y-%m-%d %H:%M:%S")

    for sensor_id, entries in sensor_hours_30d.items():
        if not entries:
            continue

        values_30d = [v for _, v in entries]
        total_30d = sum(values_30d)
        hours_count = len(values_30d)

        if hours_count < 24:
            continue  # Mindestens 1 Tag Daten nötig

        # Durchschnitt pro Stunde (letzte 30 Tage)
        avg_kwh_per_hour = total_30d / hours_count
        avg_kwh_per_day = avg_kwh_per_hour * 24

        # Prognosen
        prognose_jahr_kwh = avg_kwh_per_hour * 8760
        prognose_jahr_eur = round(prognose_jahr_kwh * strompreis, 2)
        prognose_monat_eur = round(prognose_jahr_eur / 12, 2)

        # CO₂
        co2_jahr_kg = round(prognose_jahr_kwh * co2_wert / 1000, 2)

        # Energieklasse
        if prognose_jahr_kwh < limit_a:
            klasse = "A"
        elif prognose_jahr_kwh < limit_b:
            klasse = "B"
        elif prognose_jahr_kwh < limit_c:
            klasse = "C"
        elif prognose_jahr_kwh < limit_d:
            klasse = "D"
        elif prognose_jahr_kwh < limit_e:
            klasse = "E"
        elif prognose_jahr_kwh < limit_f:
            klasse = "F"
        else:
            klasse = "G"

        # Trend: 7 Tage vs. 30 Tage
        values_7d = sensor_hours_7d.get(sensor_id, [])
        if values_7d and hours_count > len(values_7d):
            avg_7d = sum(values_7d) / len(values_7d)
            avg_30d_only = avg_kwh_per_hour
            trend_7d = round(((avg_7d - avg_30d_only) / avg_30d_only) * 100, 1) if avg_30d_only > 0 else 0.0
        else:
            trend_7d = 0.0

        # Peak-Hour: Stunde mit höchstem Durchschnitt
        hour_buckets: dict[int, list[float]] = {}
        for ts_int, value in entries:
            dt = datetime.fromtimestamp(ts_int, tz=timezone.utc)
            h = dt.hour
            if h not in hour_buckets:
                hour_buckets[h] = []
            hour_buckets[h].append(value)

        peak_hour = 0
        peak_avg = 0.0
        for h, vals in hour_buckets.items():
            h_avg = sum(vals) / len(vals)
            if h_avg > peak_avg:
                peak_avg = h_avg
                peak_hour = h

        # Base-Load: Durchschnitt der niedrigsten 20% Stundenwerte → Watt
        sorted_vals = sorted(values_30d)
        base_count = max(1, int(len(sorted_vals) * 0.2))
        base_kwh = sum(sorted_vals[:base_count]) / base_count
        base_load_w = round(base_kwh * 1000, 1)  # kWh/h → W

        prognosis_rows.append((
            sensor_id,
            round(avg_kwh_per_hour, 6),
            round(avg_kwh_per_day, 4),
            prognose_monat_eur,
            prognose_jahr_eur,
            round(prognose_jahr_kwh, 2),
            klasse,
            co2_jahr_kg,
            trend_7d,
            peak_hour,
            base_load_w,
            run_ts,
        ))

    # In DB schreiben
    if prognosis_rows:
        conn = sqlite3.connect(ANALYTICS_DB)
        cur = conn.cursor()
        cur.execute("DELETE FROM sensor_prognosis;")
        cur.executemany("""
            INSERT INTO sensor_prognosis (
                sensor_id, avg_kwh_per_hour, avg_kwh_per_day,
                prognose_monat_eur, prognose_jahr_eur, prognose_jahr_kwh,
                energieklasse, co2_jahr_kg, trend_7d, peak_hour, base_load_w, last_update
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, prognosis_rows)
        conn.commit()
        conn.close()
        logger.info(f"✅ Prognosen für {len(prognosis_rows)} Sensoren berechnet und gespeichert.")
    else:
        logger.warning("⚠️ Keine Prognosen berechnet (zu wenig Daten).")


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

        # Prognosen berechnen (immer, unabhängig vom Modus)
        calculate_prognosis()

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

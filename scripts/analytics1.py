#!/usr/bin/env python3

import os
import sqlite3
import statistics
import time
from pathlib import Path
from datetime import datetime, timezone
from dotenv import load_dotenv
from apscheduler.schedulers.blocking import BlockingScheduler

load_dotenv()

# =========================================================
# SETTINGS
# =========================================================
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / os.getenv("DATA_DIR", "data")

ANALYTICS_DB_PATH_ENV = os.getenv("ANALYTICS_DB_PATH")
if ANALYTICS_DB_PATH_ENV:
    ANALYTICS_DB = BASE_DIR / ANALYTICS_DB_PATH_ENV
else:
    ANALYTICS_DB = DATA_DIR / "analytics.sqlite"

ANALYTICS_DB.parent.mkdir(parents=True, exist_ok=True)

# =========================================================
# HELPER FUNCTIONS
# =========================================================
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
# ⚡ INTUITIVES DELTA-STREAMING (Lädt nur das Zieljahr!)
# =========================================================
def stream_hourly_values(target_year=None):
    # Wenn target_year gesetzt ist, laden wir NUR diese eine Datei (z.B. sensors_2026.db)
    if target_year:
        databases = list(DATA_DIR.glob(f"*{target_year}*.db")) + list(DATA_DIR.glob(f"*{target_year}*.sqlite"))
    else:
        # Initialer Vollaufbau (falls analytics.sqlite leer ist)
        databases = list(DATA_DIR.glob("*.sqlite")) + list(DATA_DIR.glob("*.db"))

    for db in databases:
        if db.resolve() == ANALYTICS_DB.resolve():
            continue

        conn = sqlite3.connect(db)
        cur = conn.cursor()
        try:
            cur.execute("SELECT sensor_id, consumption, hour FROM hourly_values")
        except:
            try: cur.execute("SELECT sensor_id, consumption, timestamp FROM hourly_values")
            except:
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
# SQLITE INIT
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
        CREATE TABLE IF NOT EXISTS sensor_daily (
            sensor_id TEXT, day TEXT, total REAL, average REAL, minimum_baseload REAL,
            maximum_peak REAL, load_factor REAL, samples INTEGER, is_complete INTEGER, PRIMARY KEY (sensor_id, day)
        )
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_sensor_month ON sensor_monthly(sensor_id, year)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_day ON sensor_daily(day)")
    conn.commit()
    conn.close()

# =========================================================
# CALCULATION ENGINE
# =========================================================
def calculate_analytics(target_year=None):
    yearly, monthly_data, daily_data = {}, {}, {}

    # Nutzt den optimierten Delta-Streamer
    for sensor, value, ts in stream_hourly_values(target_year):
        dt = get_utc_datetime(ts)
        if not dt: continue

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

        m_key = (sensor, dt.year, dt.month)
        monthly_data[m_key] = monthly_data.get(m_key, 0.0) + value
        y_key = (sensor, dt.year, 0)
        monthly_data[y_key] = monthly_data.get(y_key, 0.0) + value

        day_str = dt.strftime("%Y-%m-%d")
        d_key = (sensor, day_str)
        if d_key not in daily_data: daily_data[d_key] = []
        daily_data[d_key].append(value)

    return yearly, monthly_data, daily_data

# =========================================================
# WRITE TRANSACTION
# =========================================================
def save_to_db(yearly, monthly_data, daily_data, target_year=None):
    conn = sqlite3.connect(ANALYTICS_DB)
    cur = conn.cursor()
    try:
        cur.execute("BEGIN TRANSACTION;")

        # ⚡ DELTA-LOGIK: Wenn wir nur ein Jahr updaten, löschen wir auch nur dieses eine Jahr aus der DB!
        if target_year:
            cur.execute("DELETE FROM yearly_report WHERE year = ?;", (target_year,))
            cur.execute("DELETE FROM sensor_monthly WHERE year = ?;", (target_year,))
            cur.execute("DELETE FROM sensor_daily WHERE day LIKE ?;", (f"{target_year}-%",))
        else:
            cur.execute("DELETE FROM yearly_report;")
            cur.execute("DELETE FROM sensor_monthly;")
            cur.execute("DELETE FROM sensor_daily;")

        # Inserts aufbereiten und wegschreiben
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
            cur.execute("INSERT INTO yearly_report VALUES (?, ?, ?, ?, ?);", (year, len(values), total, avg_month, avg_day))

        for (sensor_id, year, month), total in monthly_data.items():
            cur.execute("INSERT INTO sensor_monthly VALUES (?, ?, ?, ?);", (sensor_id, year, month, round(total, 4)))

        for (sensor_id, day_str), values in daily_data.items():
            samples = len(values)
            day_total, day_avg = sum(values), statistics.mean(values)
            day_min, day_max = min(values), max(values)
            load_factor = round(day_avg / day_max, 4) if day_max > 0 else 0.0
            cur.execute("INSERT INTO sensor_daily VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);",
                        (sensor_id, day_str, round(day_total, 4), round(day_avg, 4), round(day_min, 4), round(day_max, 4), load_factor, samples, 1 if samples >= 24 else 0))

        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"❌ Transaktions-Fehler: {e}")
    finally:
        conn.close()

# =========================================================
# TRIGGER PIPELINE FUNCTION
# =========================================================
def run_pipeline():
    start_time = time.time()
    init_database()

    # Prüfen, ob die Analytics-DB komplett leer ist (z.B. beim ersten Docker-Start)
    conn = sqlite3.connect(ANALYTICS_DB)
    is_empty = conn.execute("SELECT COUNT(*) FROM yearly_report;").fetchone()[0] == 0
    conn.close()

    if is_empty:
        print("📥 Initialer Vollaufbau: Verarbeite alle historischen Jahre...")
        yearly, monthly, daily = calculate_analytics(target_year=None)
        save_to_db(yearly, monthly, daily, target_year=None)
    else:
        # Regulärer, täglicher Lauf: Verarbeite NUR das aktuelle Kalenderjahr
        current_year = datetime.now().year
        print(f"🔄 Tägliches Delta-Update: Berechne exklusiv das aktuelle Jahr {current_year}...")
        yearly, monthly, daily = calculate_analytics(target_year=current_year)
        save_to_db(yearly, monthly, daily, target_year=current_year)

    print(f"🏁 Pipeline erfolgreich beendet in {time.time() - start_time:.2f} Sekunden.")

# =========================================================
# APSCHEDULER BACKGROUND SERVICE
# =========================================================
if __name__ == "__main__":
    # Einmalig beim Container-Start ausführen, damit die Daten sofort aktuell sind
    run_pipeline()

    # Scheduler konfigurieren
    scheduler = BlockingScheduler()
    # Läuft jede Nacht um exakt 01:15 Uhr nachts
    scheduler.add_job(run_pipeline, 'cron', hour=1, minute=15, timezone="Europe/Berlin")

    print("⏰ Analytics-Hintergrunddienst aktiv. Warte auf den nächsten nächtlichen Lauf...")
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        print("👋 Dienst beendet.")

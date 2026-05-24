#!/usr/bin/env python3

import os
import sqlite3
import statistics

from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# =========================================================
# LOAD ENV
# =========================================================

load_dotenv()

# =========================================================
# SETTINGS
# =========================================================

BASE_DIR = Path(__file__).resolve().parent

DATA_DIR = BASE_DIR / os.getenv(
    "DATA_DIR",
    "data"
)

# Analytics DB - entweder aus ANALYTICS_DB_PATH oder fallback
ANALYTICS_DB_PATH_ENV = os.getenv("ANALYTICS_DB_PATH")
if ANALYTICS_DB_PATH_ENV:
    ANALYTICS_DB = BASE_DIR / ANALYTICS_DB_PATH_ENV
else:
    # Fallback: im DATA_DIR
    ANALYTICS_DB = DATA_DIR / "analytics.sqlite"

YEAR_FROM = int(
    os.getenv("YEAR_FROM", "1970")
)

YEAR_TO = int(
    os.getenv("YEAR_TO", "2100")
)

ENABLE_CLUSTERING = (
    os.getenv("ENABLE_CLUSTERING", "true").lower()
    == "true"
)

ENABLE_DAILY_STATS = (
    os.getenv("ENABLE_DAILY_STATS", "true").lower()
    == "true"
)

# =========================================================
# CREATE DIRECTORIES
# =========================================================

# Stelle sicher dass ANALYTICS_DB Verzeichnis existiert
ANALYTICS_DB.parent.mkdir(parents=True, exist_ok=True)


print("BASE_DIR:", BASE_DIR)
print("DATA_DIR:", DATA_DIR)
print("EXISTS:", DATA_DIR.exists())

# =========================================================
# DATABASES (KORRIGIERT: Ignoriert die analytics.sqlite selbst!)
# =========================================================

def get_databases():
    all_files = list(DATA_DIR.glob("*.sqlite")) + list(DATA_DIR.glob("*.db"))

    # 🔧 CRITICAL FIX: Verhindert, dass das Skript seine eigene Ziel-DB einliest
    return [
        f for f in all_files
        if f.resolve() != ANALYTICS_DB.resolve()
    ]

# Kleiner Log zur Kontrolle nach dem Fix
print("FILES FOR ANALYSIS:", [f.name for f in get_databases()])

# =========================================================
# FIXED YEAR PARSER (ONLY CHANGE HERE)
# =========================================================

def extract_year(ts):

    if ts is None:
        return None

    # --- FIX: hour-based data (YOUR CASE) ---
    try:
        hour = int(ts)
        return int(hour / 8760) + 1970
    except:
        pass

    # --- fallback ISO ---
    try:
        return datetime.fromisoformat(str(ts)).year
    except:
        pass

    # --- fallback string ---
    try:
        return int(str(ts)[:4])
    except:
        return None

# =========================================================
# LOAD RAW DATA
# =========================================================

def load_hourly_values():

    rows = []

    databases = get_databases()

    print(f"\nFound databases for analysis: {len(databases)}\n")

    for db in databases:

        print(f"Loading: {db.name}")

        conn = sqlite3.connect(db)
        cur = conn.cursor()

        try:

            cur.execute("""
                SELECT
                    sensor_id,
                    consumption,
                    timestamp
                FROM hourly_values
            """)

        except Exception as e:
            # Durch unseren Fix oben taucht die 'analytics.sqlite' hier gar nicht mehr auf!
            print(f"Skipping {db.name}: {e}")
            conn.close()
            continue

        for sensor, value, ts in cur.fetchall():

            if sensor is None:
                continue

            if value is None:
                continue

            try:
                value = float(value)

            except:
                continue

            year = extract_year(ts)

            if year is None:
                continue

            if year < YEAR_FROM:
                continue

            if year > YEAR_TO:
                continue

            rows.append((
                sensor,
                value,
                ts
            ))

        conn.close()

    return rows

# =========================================================
# SQLITE INIT
# =========================================================

def init_database():

    conn = sqlite3.connect(ANALYTICS_DB)

    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS yearly_report (
            year INTEGER PRIMARY KEY,
            entries INTEGER,
            total REAL,
            avg_month REAL,
            avg_day REAL
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
            sensor_id TEXT,
            day TEXT,
            total REAL,
            average REAL,
            maximum REAL,
            samples INTEGER
        )
    """)

    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_sensor
        ON sensor_clusters(sensor_id)
    """)

    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_cluster
        ON sensor_clusters(cluster)
    """)

    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_day
        ON sensor_daily(day)
    """)

    conn.commit()
    conn.close()

# =========================================================
# YEARLY ANALYSIS (FIXED: Gleiche Logik wie report.py)
# =========================================================

def build_yearly(rows):

    yearly = {}

    for sensor, value, ts in rows:

        year = extract_year(ts)

        if year is None:
            continue

        if year not in yearly:
            yearly[year] = {
                'values': [],
                'min_hour': None,
                'max_hour': None
            }

        yearly[year]['values'].append(value)

        # Speichere Min/Max Hour
        try:
            hour = int(ts)

            if yearly[year]['min_hour'] is None:
                yearly[year]['min_hour'] = hour
                yearly[year]['max_hour'] = hour
            else:
                yearly[year]['min_hour'] = min(yearly[year]['min_hour'], hour)
                yearly[year]['max_hour'] = max(yearly[year]['max_hour'], hour)
        except:
            pass

    result = []

    for year, data in yearly.items():

        values = data['values']
        total = sum(values)

        min_hour = data['min_hour']
        max_hour = data['max_hour']

        if min_hour is not None and max_hour is not None:
            # Konvertiere Hours zu Datetime
            from datetime import datetime

            start_dt = datetime.utcfromtimestamp(min_hour * 3600)
            end_dt = datetime.utcfromtimestamp(max_hour * 3600)

            # Berechne Tage
            days = (end_dt.date() - start_dt.date()).days + 1

            # Berechne Monate
            months = (
                (end_dt.year - start_dt.year) * 12 +
                (end_dt.month - start_dt.month) + 1
            )

            days = max(1, days)
            months = max(1, months)

            avg_day = total / days
            avg_month = total / months
        else:
            avg_day = 0
            avg_month = 0

        result.append((
            year,
            len(values),
            total,
            avg_month,
            avg_day
        ))

    result.sort(key=lambda x: x[0])

    return result

# =========================================================
# CLASSIFICATION (UNCHANGED)
# =========================================================

def classify(values):

    values = sorted([
        v for v in values
        if v > 0
    ])

    if not values:
        return None

    n = len(values)

    base_cut = max(1, int(n * 0.2))
    mid_cut = max(base_cut + 1, int(n * 0.9))

    base = sum(values[:base_cut])
    mid = sum(values[base_cut:mid_cut])
    peak = sum(values[mid_cut:])

    total = base + mid + peak

    if total == 0:
        return None

    # [Hier läuft dein originaler Berechnungs-Loop am Ende weiter...]

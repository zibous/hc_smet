#!/usr/bin/env python3

import os
import sys
import sqlite3
from pathlib import Path
import time
from datetime import datetime

import pandas as pd
import mysql.connector
from dotenv import load_dotenv

# =========================================================
# ARGS PARSING VERSION 3.0
# =========================================================

args = sys.argv[1:]
INCLUDE_READABLE = "--all" in args
clean_args = [a for a in args if a != "--all"]

YEARS = []

if not clean_args:
    YEARS = [datetime.now().year]
else:
    for arg in clean_args:
        if "-" in arg:
            try:
                start_year, end_year = map(int, arg.split("-"))
                YEARS.extend(list(range(start_year, end_year + 1)))
            except ValueError:
                print(f"❌ Ungültiges Range-Format: {arg}. Nutze z.B. 2024-2026")
                sys.exit(1)
        elif arg.isdigit():
            YEARS.append(int(arg))

YEARS = sorted(list(set(YEARS)))

if not YEARS:
    print("Usage:")
    print("  python getpokeydata.py 2024-2026 [--all]")
    print("  python getpokeydata.py 2026 [--all]")
    print("  python getpokeydata.py [--all]")
    sys.exit(1)

print(f"🚀 Starte Datenimport v3.0 für Jahre: {YEARS} (Readable-Columns: {INCLUDE_READABLE})")

# =========================================================
# 1. BASE ENV
# =========================================================

load_dotenv()

# ---------------------------------------------------------
# Skalierungsfaktoren für Impulszähler (kWh-Berechnung)
# ---------------------------------------------------------
#
# Alle Sensorwerte sind Impulszähler (Impulse pro Zeitintervall).
# Diese werden in Energie (kWh) umgerechnet.
#
# WICHTIG:
# Der Faktor ist NICHT "1 Impuls = Wh",
# sondern direkt: kWh pro Impuls.
# ---------------------------------------------------------

# 1000 Impulse / kWh
# => 1 Impuls = 0.001 kWh = 1 Wh
# (intern skaliert auf 0.00010 wegen System-Scaling)
# eacWSZ-50A / 1000imp/hWh
SCALE_FACTOR = float(os.getenv("SCALE_FACTOR", "0.00010"))

# 800 Impulse / kWh
# => 1 Impuls = 0.00125 kWh = 1.25 Wh
# (konsistent zur 1000er Skala hochgerechnet)
# eacDSZ-63A / 800imp/kWh
SCALE_FACTOR2 = float(os.getenv("SCALE_FACTOR2", "0.000125"))

# ---------------------------------------------------------
# Testcase
# ---------------------------------------------------------
# SELECT
#     sensor04,
#     sensor04 * 0.00010 AS kwh_estimate
# FROM pokeyslog
# WHERE dev = 'IF64'
# LIMIT 20;

# SELECT
#     sensor04,
#     sensor04 * 0.000125 AS kwh_estimate
# FROM pokeyslog
# WHERE dev = 'IF65'
# LIMIT 20;

# ---------------------------------------------------------
# Sensor-spezifische Skalierung
# ---------------------------------------------------------
# Standard-Sensoren: 1000 imp/kWh
# Hochlast-Sensoren: 800 imp/kWh
# ---------------------------------------------------------
SENSOR_SENSOR_FACTOR = {
    **{
        f"S{i:02d}": SCALE_FACTOR
        for i in range(1, 51)
        if i not in [34, 35, 36, 37, 38, 39, 40, 41, 42]
    },
    **{
        f"S{i:02d}": SCALE_FACTOR2
        for i in [34, 35, 36, 37, 38, 39, 40, 41, 42]
    },
}

# Ausgabe Verzeichnis
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "./")
Path(OUTPUT_DIR).mkdir(exist_ok=True)

SQLITE_TEMPLATE = os.getenv("SQLITE_NAME_TEMPLATE", "sensors_{year}.db")

ROUND_DIGITS = int(os.getenv("ROUND_DIGITS", "6"))

RAW_SENSORS = [f"sensor{i:02d}" for i in range(1, 26)]

# =========================================================
# 2. YEAR NORMALIZATION
# =========================================================
NORMALIZE_FACTORS_RAW = os.getenv("NORMALIZE_FACTORS", "")
normalize_map = {}
if NORMALIZE_FACTORS_RAW:
    for part in NORMALIZE_FACTORS_RAW.split(","):
        try:
            year, factor = part.split(":")
            normalize_map[int(year.strip())] = float(factor.strip())
        except:
            pass

# =========================================================
# 3. MYSQL CONNECTION
# =========================================================
mysql_conn = mysql.connector.connect(
    user=os.getenv("MYSQL_USER"),
    password=os.getenv("MYSQL_PASSWORD"),
    database=os.getenv("MYSQL_DATABASE"),
    host=os.getenv("MYSQL_HOST", "localhost"),
    port=int(os.getenv("MYSQL_PORT", 3306)),
)

total_start = time.time()

# =========================================================
# LOOP YEARS
# =========================================================

for YEAR in YEARS:

    print("\n" + "=" * 60)
    print(f"📅 VERARBEITE JAHR: {YEAR}")
    print("=" * 60)

    factor = normalize_map.get(YEAR, 1.0)

    sqlite_file = os.path.join(OUTPUT_DIR, SQLITE_TEMPLATE.format(year=YEAR))
    conn = sqlite3.connect(sqlite_file)
    cur = conn.cursor()

    cur.execute("PRAGMA journal_mode=WAL;")
    cur.execute("PRAGMA synchronous=NORMAL;")
    cur.execute("DROP TABLE IF EXISTS hourly_values;")
    cur.execute("DROP TABLE IF EXISTS sensor_state;")

    if INCLUDE_READABLE:
        cur.execute("""
            CREATE TABLE hourly_values (
                sensor_id TEXT NOT NULL,
                hour INTEGER NOT NULL,
                hour_readable TEXT,
                ts_readable TEXT,
                consumption REAL,
                total REAL,
                PRIMARY KEY (sensor_id, hour)
            )
        """)
    else:
        cur.execute("""
            CREATE TABLE hourly_values (
                sensor_id TEXT NOT NULL,
                hour INTEGER NOT NULL,
                consumption REAL NOT NULL,
                total REAL,
                PRIMARY KEY (sensor_id, hour)
            )
        """)

    query = f"""
        SELECT * FROM pokeyslog
        WHERE timestamp >= '{YEAR - 1}-12-31 00:00:00'
          AND timestamp <  '{YEAR + 1}-01-02 00:00:00'
          AND dev IN ('IF64', 'IF65')
    """

    df = pd.read_sql(query, mysql_conn)

    if df.empty:
        print(f"⚠️ Keine Daten für das Jahr {YEAR} in MySQL gefunden.")
        conn.close()
        continue

    df = df.sort_values("timestamp")

    ts_local = pd.to_datetime(df["timestamp"], errors="coerce")
    ts_utc = ts_local.dt.tz_localize(
        "Europe/Berlin",
        ambiguous="NaT",
        nonexistent="NaT"
    ).dt.tz_convert("UTC")

    df["hour_dt"] = ts_utc.dt.floor("h").dt.tz_localize(None)
    ts_utc_naive = ts_utc.dt.tz_localize(None)

    df["hour"] = df["hour_dt"].astype("int64") // 10**9
    df["timestamp"] = ts_utc_naive.astype("int64") // 10**9

    df = df[
        (df["hour_dt"] >= f"{YEAR}-01-01 00:00:00") &
        (df["hour_dt"] < f"{YEAR + 1}-01-01 00:00:00")
    ]

    if df.empty:
        print(f"⚠️ Nach UTC-Konvertierung keine Daten für das Jahr {YEAR} übrig.")
        conn.close()
        continue

    readable_mapping = {}

    if INCLUDE_READABLE:
        df["hour_readable"] = df["hour_dt"].dt.strftime("%Y-%m-%d %H:%M:%S")
        df["ts_readable"] = ts_utc_naive.dt.strftime("%Y-%m-%d %H:%M:%S")

        mapping_df = df.drop_duplicates(subset=["hour"])
        readable_mapping = dict(
            zip(mapping_df["hour"],
                zip(mapping_df["hour_readable"], mapping_df["ts_readable"]))
        )

    a = df[df["dev"] == "IF64"]
    b = df[df["dev"] == "IF65"]

    a_hour = a.groupby("hour")[RAW_SENSORS].sum() if not a.empty else pd.DataFrame(columns=RAW_SENSORS)
    b_hour = b.groupby("hour")[RAW_SENSORS].sum() if not b.empty else pd.DataFrame(columns=RAW_SENSORS)

    a_hour.columns = [f"S{i:02d}" for i in range(1, 26)]
    b_hour.columns = [f"S{i:02d}" for i in range(26, 51)]

    hourly = pd.concat([a_hour, b_hour], axis=1).fillna(0)

    insert_sql = (
        "INSERT OR REPLACE INTO hourly_values(sensor_id, hour, hour_readable, ts_readable, consumption) "
        "VALUES (?, ?, ?, ?, ?)"
        if INCLUDE_READABLE
        else
        "INSERT OR REPLACE INTO hourly_values(sensor_id, hour, consumption) VALUES (?, ?, ?)"
    )

    data = []

    for hour, row in hourly.iterrows():

        unix = int(hour)

        if INCLUDE_READABLE:
            hour_readable, ts_readable = readable_mapping.get(unix, ("-", "-"))

        for col in hourly.columns:

            value = row[col]
            if value is None or value <= 0:
                continue

            sensor_factor = SENSOR_SENSOR_FACTOR.get(col, SCALE_FACTOR)

            value = float(value) * sensor_factor * factor
            value = round(value, ROUND_DIGITS)

            if INCLUDE_READABLE:
                data.append((col, unix, hour_readable, ts_readable, value))
            else:
                data.append((col, unix, value))

    cur.executemany(insert_sql, data)
    conn.commit()

    print(f"📝 {len(data)} Zeilen erfolgreich importiert.")

    cur.execute("PRAGMA integrity_check;")
    check_result = cur.fetchone()[0]

    if check_result.lower() == "ok":
        print(f"✅ Integritätsprüfung BESTANDEN für: {sqlite_file}")
    else:
        print(f"❌ FEHLER: {check_result}")

    conn.close()

mysql_conn.close()

print("\n" + "=" * 60)
print(f"🏁 SKRIPT BEENDET - GESAMTZEIT: {time.time() - total_start:.2f}s")
print("=" * 60)

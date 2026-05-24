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

# Ausgabe Verzeichnis
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "./")
Path(OUTPUT_DIR).mkdir(exist_ok=True)

# Datenbank name
SQLITE_TEMPLATE = os.getenv("SQLITE_NAME_TEMPLATE", "sensors_{year}.db")

# Scalierungsfaktor der Werte der Spalten: z.B: kWh = 980 * 0.0001
SCALE_FACTOR = float(os.getenv("SCALE_FACTOR", "0.0001"))

# Rundungsregel für Zahlen
ROUND_DIGITS = int(os.getenv("ROUND_DIGITS", "6"))

# range(1, 26) erzeugt die Zahlen 1 bis 25.
# f"sensor{i:02d}" formatiert jede Zahl als zweistellige
# Zahl mit führender Null. z.B.: S01 ... 25
RAW_SENSORS = [f"sensor{i:02d}" for i in range(1, 26)]

# =========================================================
# 2. YEAR NORMALIZATION
#    Beispiel: { 2023: 1.2, 2024: 0.95, 2025: 0.53679 }
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

    # Jahres Korrekturfaktor und wenn nicht vorhanden 1.0
    factor = normalize_map.get(YEAR, 1.0)

    sqlite_file = os.path.join(OUTPUT_DIR, SQLITE_TEMPLATE.format(year=YEAR))
    conn = sqlite3.connect(sqlite_file)
    cur = conn.cursor()

    # Performance-Tuning
    cur.execute("PRAGMA journal_mode=WAL;")
    cur.execute("PRAGMA synchronous=NORMAL;")
    cur.execute("DROP TABLE IF EXISTS hourly_values;")
    cur.execute("DROP TABLE IF EXISTS sensor_state;")

    # Table-Creation neue Version für APP 21.05.2026 !!
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

    # -------------------------
    # Data pokeyslog mysql
    # -------------------------
    #   mode	status	timestamp	version	mac	dev	datamode	sensor01	sensor02	sensor03	sensor04	sensor05	sensor06	sensor07	sensor08	sensor09	sensor10	sensor11	sensor12	sensor13	sensor14	sensor15	sensor16	sensor17	sensor18	sensor19	sensor20	sensor21	sensor22	sensor23	sensor24	sensor25	total	year	month	week	day	hour	udate	archived
    #   result	1	2013-09-27 19:38:09	13.08.280750	50:FA:AB:00:54:48	IF64	1	0	0	0	210	20	40	0	60	0	0	20	20	140	0	0	0	0	0	0	0	0	0	10	0	0	560	2013	2013/09	2013/KW39	2013-09-27	19	2013-09-27 17:38:09	0
    #   result	1	2013-09-27 19:38:09	13.08.280750	50:FA:AB:00:54:47	IF65	1	0	0	0	10	10	0	610	50	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	680	2013	2013/09	2013/KW39	2013-09-27	19	2013-09-27 17:38:09	0
    #   result	1	2013-09-27 20:00:09	13.08.280750	50:FA:AB:00:54:48	IF64	1	0	0	0	130	120	30	80	80	100	0	20	40	30	0	0	10	0	0	0	0	0	0	30	0	0	730	2013	2013/09	2013/KW39	2013-09-27	20	2013-09-27 18:00:09	0
    #   result	1	2013-09-27 20:00:09	13.08.280750	50:FA:AB:00:54:47	IF65	1	0	0	0	20	20	0	770	90	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	900	2013	2013/09	2013/KW39	2013-09-27	20	2013-09-27 18:00:09	0
    #   result	1	2013-09-27 20:30:09	13.08.280750	50:FA:AB:00:54:48	IF64	1	0	0	0	90	120	20	0	120	240	0	300	60	0	0	0	10	0	0	0	0	0	0	40	0	0	1050	2013	2013/09	2013/KW39	2013-09-27	20	2013-09-27 18:30:09	0
    #   result	1	2013-09-27 20:30:09	13.08.280750	50:FA:AB:00:54:47	IF65	1	0	0	0	20	20	0	980	220	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	1240	2013	2013/09	2013/KW39	2013-09-27	20	2013-09-27 18:30:09	0
    #   result	1	2013-09-27 21:00:09	13.08.280750	50:FA:AB:00:54:48	IF64	1	0	0	0	100	20	10	0	110	250	0	330	50	0	0	0	0	0	0	0	0	0	0	40	0	0	910	2013	2013/09	2013/KW39	2013-09-27	21	2013-09-27 19:00:09	0
    #   result	1	2013-09-27 21:00:09	13.08.280750	50:FA:AB:00:54:47	IF65	1	0	0	0	30	30	0	1010	120	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	1190	2013	2013/09	2013/KW39	2013-09-27	21	2013-09-27 19:00:09	0
    #   result	1	2013-09-27 21:30:09	13.08.280750	50:FA:AB:00:54:48	IF64	1	0	0	0	90	120	0	0	110	240	60	320	60	0	0	0	0	0	0	0	0	0	0	30	0	0	1030	2013	2013/09	2013/KW39	2013-09-27	21	2013-09-27 19:30:09	0
    #   result	1	2013-09-27 21:30:09	13.08.280750	50:FA:AB:00:54:47	IF65	1	0	0	0	20	20	0	960	120	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	1120	2013	2013/09	2013/KW39	2013-09-27	21	2013-09-27 19:30:09	0

    # Data-Load mit Puffer am Jahresrand (Wichtig, da Berlin-Zeit vor UTC liegt)
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

    # =====================================================
    # ⚡ TIME-PROCESSING (UMRECHNUNG IN UTC via PANDAS)
    #   Timestamp ist der Zeitstempel der Messung
    # =====================================================
    df = df.sort_values("timestamp")

    # 1. Spalte als Datetime einlesen
    ts_local = pd.to_datetime(df["timestamp"], errors="coerce")

    # 2. Lokale Berliner Zeit zuweisen und präzise in UTC konvertieren
    ts_utc = ts_local.dt.tz_localize("Europe/Berlin", ambiguous="NaT", nonexistent="NaT").dt.tz_convert("UTC")

    # 3. Zeitzonen-Stempel entfernen, damit Unix-Timestamp-Berechnung stimmt
    df["hour_dt"] = ts_utc.dt.floor("h").dt.tz_localize(None)
    ts_utc_naive = ts_utc.dt.tz_localize(None)

    # 4. UNIX-Timestamps generieren (jetzt echt in UTC)
    df["hour"] = df["hour_dt"].astype("int64") // 10**9
    df["timestamp"] = ts_utc_naive.astype("int64") // 10**9

    # 5. Nach der UTC-Umrechnung filtern wir hier hart auf das aktuelle Zieljahr
    df = df[(df["hour_dt"] >= f"{YEAR}-01-01 00:00:00") & (df["hour_dt"] < f"{YEAR + 1}-01-01 00:00:00")]

    if df.empty:
        print(f"⚠️ Nach UTC-Konvertierung keine Daten für das Jahr {YEAR} übrig.")
        conn.close()
        continue

    # HIGH-SPEED FIX: Wir bauen ein blitzschnelles Index-Mapping im RAM
    readable_mapping = {}

    if INCLUDE_READABLE:
        df["hour_readable"] = df["hour_dt"].dt.strftime("%Y-%m-%d %H:%M:%S")
        df["ts_readable"] = ts_utc_naive.dt.strftime("%Y-%m-%d %H:%M:%S")

        mapping_df = df.drop_duplicates(subset=["hour"])
        readable_mapping = dict(zip(mapping_df["hour"], zip(mapping_df["hour_readable"], mapping_df["ts_readable"])))

    # Split Devices
    a = df[df["dev"] == "IF64"]
    b = df[df["dev"] == "IF65"]

    a_hour = a.groupby("hour")[RAW_SENSORS].sum() if not a.empty else pd.DataFrame(columns=RAW_SENSORS)
    b_hour = b.groupby("hour")[RAW_SENSORS].sum() if not b.empty else pd.DataFrame(columns=RAW_SENSORS)

    a_hour.columns = [f"S{i:02d}" for i in range(1, 26)]
    b_hour.columns = [f"S{i:02d}" for i in range(26, 51)]

    hourly = pd.concat([a_hour, b_hour], axis=1).fillna(0)

    # Insert Statements
    if INCLUDE_READABLE:
        insert_sql = "INSERT OR REPLACE INTO hourly_values(sensor_id, hour, hour_readable, ts_readable, consumption) VALUES (?, ?, ?, ?, ?)"
    else:
        insert_sql = "INSERT OR REPLACE INTO hourly_values(sensor_id, hour, consumption) VALUES (?, ?, ?)"

    # Build Insert Array
    data = []
    for hour, row in hourly.iterrows():

        unix = int(hour)

        if INCLUDE_READABLE:
            hour_readable, ts_readable = readable_mapping.get(unix, ("-", "-"))

        for col in hourly.columns:

            value = row[col]
            if value is None or value <= 0:
                continue

            value = float(value) * SCALE_FACTOR * factor
            value = round(value, ROUND_DIGITS)

            if INCLUDE_READABLE:
                data.append((col, unix, hour_readable, ts_readable, value))
            else:
                data.append((col, unix, value))

    # Bulk-Insert ausführen
    cur.executemany(insert_sql, data)
    conn.commit()
    print(f"📝 {len(data)} Zeilen erfolgreich importiert.")

    # =====================================================
    # AUTOMATISCHER INTEGRITÄTS-CHECK
    # =====================================================
    print("🔍 Starte Datenbank-Integritätsprüfung...")
    cur.execute("PRAGMA integrity_check;")
    check_result = cur.fetchone()[0]

    if check_result.lower() == "ok":
        print(f"✅ Integritätsprüfung BESTANDEN für: {sqlite_file}")
    else:
        print(f"❌ KRITISCHER FEHLER: Datenbank {sqlite_file} ist beschädigt!")
        print(f"Details: {check_result}")

    conn.close()

mysql_conn.close()

print("\n" + "=" * 60)
print(f"🏁 SKRIPT BEENDET - GESAMTZEIT: {time.time() - total_start:.2f}s")
print("=" * 60)

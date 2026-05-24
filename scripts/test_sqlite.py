#!/usr/bin/env python3
import sqlite3
from datetime import datetime

# Pfad zu deiner generierten SQLite-Datei (passe das Jahr an, wenn nötig)
SQLITE_FILE = "./data//sensors_2026.db"

conn = sqlite3.connect(SQLITE_FILE)
cur = conn.cursor()

print(f"🔍 Starte Test für SQLite-Datenbank: {SQLITE_FILE}\n")

# TEST 1: Anzahl der Einträge pro Sensor zählen
print("--- TEST 1: Datendichte prüfen ---")
cur.execute("""
    SELECT sensor_id, COUNT(DISTINCT hour) as stunden_anzahl
    FROM hourly_values
    GROUP BY sensor_id
    LIMIT 5;
""")
for row in cur.fetchall():
    print(f"Sensor: {row[0]} hat {row[1]} aufgezeichnete Stunden.")

# TEST 2: Den allerersten und allerletzten Eintrag prüfen
print("\n--- TEST 2: Jahresränder prüfen (Sollte UTC sein) ---")
cur.execute("""
    SELECT MIN(hour), MAX(hour) FROM hourly_values;
""")
min_ts, max_ts = cur.fetchone()

if min_ts and max_ts:
    # Alt: nutzt lokale PC-Zeit
    # first_hour = datetime.fromtimestamp(min_ts, tz=None)

    # Neu: Erzwingt die Anzeige in echtem UTC
    from datetime import timezone
    first_hour = datetime.fromtimestamp(min_ts, tz=timezone.utc)
    last_hour = datetime.fromtimestamp(max_ts, tz=timezone.utc)


    print(f"Erster UTC-Zeitstempel im Unix-Format: {min_ts}")
    print(f"Letzter UTC-Zeitstempel im Unix-Format: {max_ts}")
    print(f"Umgerechnet erster Eintrag (Stunde):    {first_hour.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Umgerechnet letzter Eintrag (Stunde):    {last_hour.strftime('%Y-%m-%d %H:%M:%S')}")
else:
    print("⚠️ Keine Daten in der Tabelle 'hourly_values' gefunden.")

# TEST 3: Stichprobe der gespeicherten Werte
print("\n--- TEST 3: Stichprobe der Daten ---")
cur.execute("SELECT * FROM hourly_values LIMIT 3;")
columns = [desc[0] for desc in cur.description]
for row in cur.fetchall():
    print(dict(zip(columns, row)))

conn.close()
print("\n✅ Test beendet.")

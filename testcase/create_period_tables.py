#!/usr/bin/env python3
"""
Erstellt daily_values, weekly_values, monthly_values aus hourly_values

Aggregiert bestehende Stunden-Daten zu Tages-, Wochen- und Monats-Werten.
Kann auf bestehende Datenbanken angewendet werden.

Usage:
    python3 create_period_tables.py [path/to/data/dir]

    Ohne Argument: ./data/
    Mit Argument: angegebenes Verzeichnis
"""

import sqlite3
import sys
from pathlib import Path
from datetime import datetime
from collections import defaultdict


def create_period_tables(db_path: Path):
    """
    Erstellt Perioden-Tabellen aus hourly_values

    Args:
        db_path: Pfad zur sensors_YYYY.db Datei
    """
    print(f"\n{'='*60}")
    print(f"Verarbeite: {db_path.name}")
    print(f"{'='*60}")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 1. Prüfe ob hourly_values existiert
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='hourly_values'")
    if not cursor.fetchone():
        print("❌ Keine hourly_values Tabelle gefunden")
        conn.close()
        return

    # 2. Erstelle Tabellen-Schema
    print("\n📋 Erstelle Tabellen-Schema...")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS daily_values (
            sensor_id TEXT NOT NULL,
            day TEXT NOT NULL,
            consumption REAL,
            timestamp TEXT,
            PRIMARY KEY (sensor_id, day)
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_daily_sensor_day ON daily_values(sensor_id, day)")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS weekly_values (
            sensor_id TEXT NOT NULL,
            week TEXT NOT NULL,
            consumption REAL,
            timestamp TEXT,
            PRIMARY KEY (sensor_id, week)
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_weekly_sensor_week ON weekly_values(sensor_id, week)")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS monthly_values (
            sensor_id TEXT NOT NULL,
            month TEXT NOT NULL,
            consumption REAL,
            timestamp TEXT,
            PRIMARY KEY (sensor_id, month)
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_monthly_sensor_month ON monthly_values(sensor_id, month)")

    conn.commit()
    print("✅ Tabellen erstellt")

    # 3. Lade alle hourly_values
    print("\n📊 Lade hourly_values...")
    cursor.execute("SELECT sensor_id, hour, consumption FROM hourly_values ORDER BY hour")
    rows = cursor.fetchall()

    if not rows:
        print("❌ Keine Daten in hourly_values")
        conn.close()
        return

    print(f"✅ {len(rows)} Stunden-Einträge geladen")

    # 4. Aggregiere nach Perioden
    print("\n🔄 Aggregiere Daten...")

    daily_data = defaultdict(lambda: defaultdict(float))
    weekly_data = defaultdict(lambda: defaultdict(float))
    monthly_data = defaultdict(lambda: defaultdict(float))

    for sensor_id, hour, consumption in rows:
        if consumption is None or consumption <= 0:
            continue

        # Konvertiere hour zu INTEGER (falls als String gespeichert)
        try:
            if isinstance(hour, str):
                # Versuche als Integer zu parsen
                hour_int = int(hour)
            else:
                hour_int = int(hour)
        except (ValueError, TypeError):
            # Wenn hour ein Datetime-String ist (z.B. "2026-05-13 10:00:00")
            try:
                dt = datetime.strptime(hour, "%Y-%m-%d %H:%M:%S")
                ts = int(dt.timestamp())
                hour_int = (ts // 3600) * 3600
            except:
                print(f"⚠ Überspringe ungültigen hour-Wert: {hour}")
                continue

        # Konvertiere hour_int zu datetime
        dt = datetime.fromtimestamp(hour_int * 3600)

        # Perioden-Keys
        day_key = dt.strftime("%Y-%m-%d")
        week_key = dt.strftime("%Y-W%W")
        month_key = dt.strftime("%Y-%m")

        # Summiere consumption pro Periode
        daily_data[sensor_id][day_key] += consumption
        weekly_data[sensor_id][week_key] += consumption
        monthly_data[sensor_id][month_key] += consumption

    # 5. Schreibe daily_values
    print("\n💾 Schreibe daily_values...")
    daily_count = 0
    for sensor_id, days in daily_data.items():
        for day_key, total_consumption in days.items():
            cursor.execute("""
                INSERT OR REPLACE INTO daily_values
                (sensor_id, day, consumption, timestamp)
                VALUES (?, ?, ?, ?)
            """, (sensor_id, day_key, round(total_consumption, 3), day_key))
            daily_count += 1

    conn.commit()
    print(f"✅ {daily_count} Tages-Einträge geschrieben")

    # 6. Schreibe weekly_values
    print("\n💾 Schreibe weekly_values...")
    weekly_count = 0
    for sensor_id, weeks in weekly_data.items():
        for week_key, total_consumption in weeks.items():
            cursor.execute("""
                INSERT OR REPLACE INTO weekly_values
                (sensor_id, week, consumption, timestamp)
                VALUES (?, ?, ?, ?)
            """, (sensor_id, week_key, round(total_consumption, 3), week_key))
            weekly_count += 1

    conn.commit()
    print(f"✅ {weekly_count} Wochen-Einträge geschrieben")

    # 7. Schreibe monthly_values
    print("\n💾 Schreibe monthly_values...")
    monthly_count = 0
    for sensor_id, months in monthly_data.items():
        for month_key, total_consumption in months.items():
            cursor.execute("""
                INSERT OR REPLACE INTO monthly_values
                (sensor_id, month, consumption, timestamp)
                VALUES (?, ?, ?, ?)
            """, (sensor_id, month_key, round(total_consumption, 3), month_key))
            monthly_count += 1

    conn.commit()
    print(f"✅ {monthly_count} Monats-Einträge geschrieben")

    # 8. Statistiken
    print("\n📈 Statistiken:")
    cursor.execute("SELECT COUNT(*) FROM hourly_values")
    hourly_rows = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM daily_values")
    daily_rows = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM weekly_values")
    weekly_rows = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM monthly_values")
    monthly_rows = cursor.fetchone()[0]

    print(f"  Hourly:  {hourly_rows:>8} Einträge")
    print(f"  Daily:   {daily_rows:>8} Einträge")
    print(f"  Weekly:  {weekly_rows:>8} Einträge")
    print(f"  Monthly: {monthly_rows:>8} Einträge")
    print(f"  Total:   {hourly_rows + daily_rows + weekly_rows + monthly_rows:>8} Einträge")

    conn.close()
    print("\n✅ Fertig!")


def main():
    """Hauptfunktion"""

    # Verzeichnis bestimmen
    if len(sys.argv) > 1:
        data_dir = Path(sys.argv[1])
    else:
        data_dir = Path(__file__).parent / "data"

    if not data_dir.exists():
        print(f"❌ Verzeichnis nicht gefunden: {data_dir}")
        sys.exit(1)

    print(f"\n🔍 Suche Datenbanken in: {data_dir}")

    # Finde alle sensors_*.db Dateien
    db_files = sorted(data_dir.glob("sensors_*.db"))

    if not db_files:
        print(f"❌ Keine sensors_*.db Dateien gefunden")
        sys.exit(1)

    print(f"✅ {len(db_files)} Datenbank(en) gefunden")

    # Verarbeite jede Datenbank
    for db_file in db_files:
        try:
            create_period_tables(db_file)
        except Exception as e:
            print(f"\n❌ Fehler bei {db_file.name}: {e}")
            import traceback
            traceback.print_exc()

    print(f"\n{'='*60}")
    print("🎉 Alle Datenbanken verarbeitet!")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Vergleicht die PoKey-Logdaten mit den hourly_values in der DB.

Berechnet für jeden Sensor das erwartete Delta pro Stunde aus den
Rohdaten (PoKey*.log) und vergleicht es mit dem tatsächlichen Wert
in hourly_values.

Verwendung:
    python3 scripts/verify_hourly.py [SENSOR] [STUNDE_UTC]

Beispiele:
    python3 scripts/verify_hourly.py                    # Alle Sensoren, letzte Stunde
    python3 scripts/verify_hourly.py S32                # Nur S32, letzte Stunde
    python3 scripts/verify_hourly.py S32 1779346800     # S32, bestimmte Stunde
"""

import sqlite3
import sys
from pathlib import Path
from datetime import datetime, timezone

# Pfade
BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "sensors_2026.db"
LOG_DIR = BASE_DIR / "logs"

def parse_log_file(log_file: Path) -> list[tuple[int, dict[str, float]]]:
    """Parst eine PoKey*.log Datei und gibt [(timestamp, {sensor_id: value})] zurück."""
    entries = []
    for line in log_file.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        parts = line.split(", ", 2)
        if len(parts) < 3:
            continue
        try:
            ts = int(parts[0].strip())
        except ValueError:
            continue

        data_str = parts[2].replace("data=", "")
        sensors = {}
        for pair in data_str.split(";"):
            if "=" not in pair:
                continue
            key, val = pair.split("=", 1)
            key = key.strip()
            try:
                sensors[key] = float(val)
            except ValueError:
                continue
        entries.append((ts, sensors))
    return entries


def get_hourly_from_log(entries: list, sensor_id: str, target_hour: int) -> dict:
    """Berechnet das erwartete Delta für einen Sensor in einer bestimmten Stunde aus den Logs."""
    hour_end = target_hour + 3600

    # Alle Einträge in dieser Stunde für diesen Sensor
    values_in_hour = []
    last_before_hour = None

    for ts, sensors in entries:
        if sensor_id not in sensors:
            continue
        val = sensors[sensor_id]
        if val == 0.0:
            continue

        if ts < target_hour:
            last_before_hour = (ts, val)
        elif target_hour <= ts < hour_end:
            values_in_hour.append((ts, val))

    if not values_in_hour:
        return {"expected_delta": 0.0, "first": None, "last": None, "count": 0}

    first_val = values_in_hour[0][1]
    last_val = values_in_hour[-1][1]

    # Delta = letzter Wert in der Stunde - erster Wert in der Stunde
    # Oder: letzter Wert - letzter Wert VOR der Stunde (wenn vorhanden)
    if last_before_hour:
        expected_delta = round(last_val - last_before_hour[1], 6)
    else:
        expected_delta = round(last_val - first_val, 6)

    return {
        "expected_delta": max(expected_delta, 0.0),
        "first": first_val,
        "last": last_val,
        "last_before": last_before_hour[1] if last_before_hour else None,
        "count": len(values_in_hour),
    }


def get_db_value(sensor_id: str, hour: int) -> float | None:
    """Liest den consumption-Wert aus hourly_values."""
    conn = sqlite3.connect(str(DB_PATH))
    row = conn.execute(
        "SELECT consumption, total FROM hourly_values WHERE sensor_id=? AND hour=?",
        (sensor_id, hour)
    ).fetchone()
    conn.close()
    if row:
        return {"consumption": row[0], "total": row[1]}
    return None


def main():
    # Args parsen
    sensor_filter = None
    target_hour = None

    if len(sys.argv) > 1:
        sensor_filter = sys.argv[1]
    if len(sys.argv) > 2:
        target_hour = int(sys.argv[2])

    # Wenn keine Stunde angegeben, letzte abgeschlossene Stunde nehmen
    if target_hour is None:
        import time
        now = int(time.time())
        target_hour = ((now // 3600) - 1) * 3600

    hour_dt = datetime.fromtimestamp(target_hour, tz=timezone.utc)
    print(f"{'='*70}")
    print(f"  VERIFIKATION: hourly_values vs. PoKey-Logs")
    print(f"  Stunde: {target_hour} = {hour_dt.strftime('%Y-%m-%d %H:%M')} UTC")
    print(f"{'='*70}\n")

    # Alle Log-Dateien laden
    all_entries = []
    for log_file in sorted(LOG_DIR.glob("PoKey*.log")):
        entries = parse_log_file(log_file)
        all_entries.extend(entries)
        print(f"  📄 {log_file.name}: {len(entries)} Einträge geladen")

    all_entries.sort(key=lambda x: x[0])
    print()

    # Alle Sensoren ermitteln
    all_sensors = set()
    for _, sensors in all_entries:
        all_sensors.update(sensors.keys())

    if sensor_filter:
        all_sensors = {s for s in all_sensors if s == sensor_filter}

    # Vergleich
    print(f"  {'Sensor':<8} {'Log-Delta':>10} {'DB-Wert':>10} {'Diff':>10} {'Status':<10}")
    print(f"  {'-'*8} {'-'*10} {'-'*10} {'-'*10} {'-'*10}")

    issues = 0
    for sensor_id in sorted(all_sensors):
        log_data = get_hourly_from_log(all_entries, sensor_id, target_hour)
        db_data = get_db_value(sensor_id, target_hour)

        expected = log_data["expected_delta"]
        actual = db_data["consumption"] if db_data else 0.0

        diff = round(actual - expected, 6)
        ok = abs(diff) < 0.01  # Toleranz 0.01 kWh

        status = "✓" if ok else "⚠️ ABWEICHUNG"
        if not ok:
            issues += 1

        if expected > 0 or actual > 0:
            print(f"  {sensor_id:<8} {expected:>10.4f} {actual:>10.4f} {diff:>+10.4f} {status}")

    print(f"\n{'='*70}")
    if issues == 0:
        print(f"  ✅ Alle Werte stimmen überein.")
    else:
        print(f"  ⚠️  {issues} Abweichung(en) gefunden!")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()

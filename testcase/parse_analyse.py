import os
from pathlib import Path
from datetime import datetime

# Pfad zu deinen .log Dateien
LOG_DIR = Path("../logs")

def analyze_logs():
    # Filtert exakt nur deine PoKeys-Logdateien heraus
    log_files = list(LOG_DIR.glob("PoKey*.log"))

    if not log_files:
        print(f"❌ Keine PoKey-Logdateien (PoKey*.log) im Ordner '{LOG_DIR}' gefunden.")
        return

    all_entries = []

    # 1. Schritt: Alle Einträge einlesen
    for log_file in log_files:
        device_name = log_file.stem
        with open(log_file, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line or ", " not in line:
                    continue

                parts = line.split(", ", 2)
                if len(parts) < 3:
                    continue

                utc_seconds, local_time_str, raw_body = parts
                all_entries.append({
                    "utc": int(utc_seconds),
                    "local_time": datetime.strptime(local_time_str, "%Y-%m-%d %H:%M:%S"),
                    "device": device_name,
                    "body": raw_body
                })

    # 2. Schritt: Chronologisch nach UTC sortieren
    all_entries.sort(key=lambda x: x["utc"])

    # Speicherstrukturen
    last_sensor_values = {}  # Merkt sich den letzten Stand: {"S01": 948.43}

    # Hier strukturieren wir: { "S01": { ("2026-05-21", "07"): 0.15 } }
    sensor_hourly_consumption = {}

    # Für die finale Gesamtzusammenfassung: { ("2026-05-21", "07"): 0.30 }
    total_hourly_consumption = {}

    # 3. Schritt: Deltas berechnen
    for entry in all_entries:
        body_clean = entry["body"].replace("data=", "").strip()
        if not body_clean:
            continue

        pairs = body_clean.split(";")

        for pair in pairs:
            if "=" not in pair:
                continue
            sensor_id, val_str = pair.split("=", 1)

            try:
                current_value = float(val_str)
            except ValueError:
                continue

            if sensor_id in last_sensor_values:
                previous_value = last_sensor_values[sensor_id]
                delta = current_value - previous_value

                if delta > 0:
                    date_key = entry["local_time"].strftime("%Y-%m-%d")
                    hour_key = entry["local_time"].strftime("%H")
                    group_key = (date_key, hour_key)

                    # A) Pro Sensor speichern
                    if sensor_id not in sensor_hourly_consumption:
                        sensor_hourly_consumption[sensor_id] = {}

                    sensor_hourly_consumption[sensor_id][group_key] = \
                        sensor_hourly_consumption[sensor_id].get(group_key, 0.0) + delta

                    # B) Für Gesamtzusammenfassung aufsummieren
                    total_hourly_consumption[group_key] = \
                        total_hourly_consumption.get(group_key, 0.0) + delta

            last_sensor_values[sensor_id] = current_value

    if not total_hourly_consumption:
        print("ℹ️ Keine Verbrauchsdifferenzen (> 0) in den Logdaten gefunden.")
        return

    # 4. Schritt: AUSGABE PRO SENSOR
    print("\n📊 DETAILLIERTE AUSWERTUNG PRO SENSOR")

    # Sensoren alphabetisch sortiert durchgehen (S01, S02...)
    for sensor_id in sorted(sensor_hourly_consumption.keys()):
        print("\n" + f"=== SENSOR: {sensor_id} " + "="*38)
        print(f"{'DATUM':<12} | {'STUNDE':<6} | {'kWh (Delta)':<12} | {'TOTAL':<12}")
        print("-"*55)

        sensor_total = 0.0
        for (date, hour), kwh in sorted(sensor_hourly_consumption[sensor_id].items()):
            sensor_total += kwh
            print(f"{date:<12} | {hour:<6} | {kwh:<12.2f} | {sensor_total:<12.2f}")

    # 5. Schritt: FINALE ZUSAMMENFASSUNG (ÜBER ALLE SENSOREN)
    print("\n" + "="*55)
    print("🏆 GESAMTZUSAMMENFASSUNG (ALLE SENSOREN)")
    print("="*55)
    print(f"{'DATUM':<12} | {'STUNDE':<6} | {'kWh (Delta)':<12} | {'TOTAL':<12}")
    print("="*55)

    running_total = 0.0
    for (date, hour), kwh in sorted(total_hourly_consumption.items()):
        running_total += kwh
        print(f"{date:<12} | {hour:<6} | {kwh:<12.2f} | {running_total:<12.2f}")

    print("="*55 + "\n")

if __name__ == "__main__":
    analyze_logs()

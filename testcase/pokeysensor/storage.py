# storage.py
import json
import os
import tempfile

class StorageHandler:
    def __init__(self, filename):
        self.filename = filename

    def load(self, sensors):
        try:
            with open(self.filename, "r") as f:
                data = json.load(f)

            for sid, sensor in sensors.items():
                if sid in data:
                    saved = data[sid]

                    # Nur Messwerte laden
                    sensor.total_kwh = saved.get("total_kwh", sensor.total_kwh)
                    sensor.verbrauch_kwh = saved.get("verbrauch_kwh", sensor.verbrauch_kwh)
                    sensor.last_online_ts = saved.get("last_online_ts", sensor.last_online_ts)
                    sensor.online = saved.get("online", sensor.online)

        except FileNotFoundError:
            pass
        except json.JSONDecodeError:
            # Datei beschädigt → ignorieren
            pass

    def save(self, sensors):
        # Nur Messwerte speichern
        out = {
            sid: {
                "total_kwh": s.total_kwh,
                "verbrauch_kwh": s.verbrauch_kwh,
                "last_online_ts": s.last_online_ts,
                "online": s.online
            }
            for sid, s in sensors.items()
        }

        # 1. Temporäre Datei im gleichen Verzeichnis erzeugen
        dir_name = os.path.dirname(self.filename) or "."
        fd, tmp_path = tempfile.mkstemp(dir=dir_name)

        try:
            with os.fdopen(fd, "w") as tmp_file:
                json.dump(out, tmp_file, indent=2)
                tmp_file.flush()
                os.fsync(tmp_file.fileno())  # 2. Physisch auf Platte schreiben

            # 3. Atomar ersetzen
            os.replace(tmp_path, self.filename)

        except Exception:
            # Falls etwas schiefgeht → temporäre Datei löschen
            try:
                os.remove(tmp_path)
            except OSError:
                pass
            raise

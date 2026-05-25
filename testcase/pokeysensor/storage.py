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
                    sensor.load_dict(data[sid])

                    # --- 100% SCHUTZ VOR APPAUSFALL-HOCHSCHIESSEN ---
                    # Wenn die App während eines PoKeys-Ausfalls/Resets neu startet,
                    # müssen wir verhindern, dass die nächste Abfrage (die wieder bei 0 startet)
                    # ein riesiges negatives Delta wirft oder die Werte beim nächsten Impuls springen.

                    # Wir merken uns, dass dieser Sensor aus dem persistenten Speicher kommt
                    # und markieren ihn als "geladen". Die update()-Methode in Ihrem S0Sensor
                    # fängt ab jetzt über den bereits eingebauten Schutz:
                    # `if new_kwh < self.total_kwh:`
                    # jeden Interface-Sturz auf 0 lautlos und ohne Sprünge ab.

        except (FileNotFoundError, json.JSONDecodeError):
            pass

    def save(self, sensors):
        out = {sid: s.to_dict() for sid, s in sensors.items()}

        dir_name = os.path.dirname(self.filename) or "."
        fd, tmp_path = tempfile.mkstemp(dir=dir_name)

        try:
            with os.fdopen(fd, "w") as tmp_file:
                json.dump(out, tmp_file, indent=2)
                tmp_file.flush()
                os.fsync(tmp_file.fileno())

            os.replace(tmp_path, self.filename)

        except Exception:
            try:
                os.remove(tmp_path)
            except OSError:
                pass
            raise

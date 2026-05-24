# manager.py
from sensor import S0Sensor
from storage import StorageHandler
from network import NetworkClient
import time
import yaml
import os

class PoKeysManager:

    def __init__(self):

        # Geräte (PoKeys)
        # TODO: nicht hardcored - aus app_config.py laden !!!

        self.devices = {
            "Z1": "10.1.1.64",
            "Z2": "10.1.1.65"
        }

        self.network = NetworkClient()

        filename = os.path.splitext(os.path.basename(__file__))[0] + ".json"
        self.storage = StorageHandler(filename)

        self.sensors = {}
        self.letztes_update = "Noch keine Daten empfangen"

        # --- YAML laden ---
        with open("house.yaml") as f:
            cfg = yaml.safe_load(f)

        sensor_cfg = cfg["sensors"]

        # --- Sensoren aus YAML erzeugen ---
        for sid, data in sensor_cfg.items():

            name = data["name"]
            impulse = data["impulse"]
            model = data["model"]
            room = data.get("room")
            devices = data.get("devices", [])

            sensor = S0Sensor(name, impulse)

            # zusätzliche Metadaten am Sensor speichern
            sensor.model = model
            sensor.room = room
            sensor.devices = devices

            self.sensors[sid] = sensor

        # gespeicherte Werte laden
        self.storage.load(self.sensors)

    def update_sensors(self):

        self.letztes_update = time.strftime('%Y-%m-%d %H:%M:%S')

        for dev, ip in self.devices.items():

            result = self.network.fetch(ip)

            # Gerät offline → alle Sensoren dieses Geräts offline setzen
            if not result["online"]:
                for sid, sensor in self.sensors.items():
                    if dev in sensor.devices:
                        sensor.online = False
                continue

            # Gerät online
            data = result["data"]

            for s in data.get("sensors", []):
                sid = s["ID"]
                val = s["Val"]

                if sid in self.sensors:
                    sensor = self.sensors[sid]
                    sensor.online = True
                    sensor.last_online_ts = time.time()
                    sensor.update(val)

        self.storage.save(self.sensors)

    def get_all_data(self):

        now = time.time()
        out = {}

        for sid, s in self.sensors.items():
            d = s.to_dict()
            if d["online"]:
                d["status"] = "OK"
            else:
                offline_secs = int(now - d.get("last_online_ts", now))
                d["status"] = f"OFF {offline_secs}s"
            out[sid] = d

        return out

    def get_single_value(self, sid: str):
        return self.sensors.get(sid.upper())

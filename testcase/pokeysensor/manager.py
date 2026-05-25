# manager.py
import time
import yaml
import os

from sensor import S0Sensor
from storage import StorageHandler
from network import NetworkClient
from pokeydevice import PoKeysDevice


class PoKeysManager:

    def __init__(self):

        # --- 2 PoKeys-Interfaces definieren ---
        # Jedes Interface liefert 25 Sensoren

        # see app_config.py:
        #  - POKEYS_DEVICE1_NAME, POKEYS_DEVICE2_NAME
        #  - POKEYS_DEVICE1_IP, POKEYS_DEVICE2_IP
        #  - POKEYS_DEVICE1_SENSORS, POKEYS_DEVICE2_SENSORS

        self.devices = [
            PoKeysDevice("poKey64", "10.1.1.64", 1, 25),
            PoKeysDevice("poKey65", "10.1.1.65", 26, 50)
        ]

        self.network = NetworkClient()

        filename = os.path.splitext(os.path.basename(__file__))[0] + ".json"
        self.storage = StorageHandler(filename)

        self.sensors = {}
        self.letztes_update = "Noch keine Daten empfangen"

        # --- YAML laden ---
        with open("house.yaml") as f:
            cfg = yaml.safe_load(f)

        sensor_cfg = cfg["sensors"]

        # --- Sensoren erzeugen ---
        for sid, data in sensor_cfg.items():

            name = data["name"]
            impulse = data["impulse"]
            model = data["model"]
            room = data.get("room")
            devices = data.get("devices", [])

            sensor = S0Sensor(name, impulse)

            sensor.model = model
            sensor.room = room
            sensor.devices = devices
            sensor.interface = ""
            sensor.pin = None

            self.sensors[sid] = sensor

        # --- Sensoren automatisch PoKeys-Interfaces zuordnen ---
        for sid, sensor in self.sensors.items():
            num = int(sid[1:])  # "S34" → 34
            for dev in self.devices:
                if dev.start_id <= num <= dev.end_id:
                    dev.sensors.append(sid)
                    sensor.interface= dev.id
                    break

        # --- Pin-Zuordnung app_config.py ---
        # see: POKEYS_DEVICE1_PINS, POKEYS_DEVICE2_PINS
        self.pin_order = [
            0, 1, 4, 5, 8, 10, 14, 15, 18, 19,
            20, 21, 22, 23, 24, 25, 26, 27,
            40, 41, 42, 43, 45, 47, 48
        ]

        for dev in self.devices:
            dev.sensors.sort()  # S01..S25 / S26..S50
            for index, sid in enumerate(dev.sensors):
                pin = self.pin_order[index]
                self.sensors[sid].pin = pin

        # gespeicherte Werte laden
        self.storage.load(self.sensors)

    # ----------------------------------------------------------------------

    def update_sensors(self):

        self.letztes_update = time.strftime('%Y-%m-%d %H:%M:%S')

        for dev in self.devices:
            result = self.network.fetch(dev.ip)
            # Gerät offline
            if not result["online"]:
                dev.mark_offline()
                for sid in dev.sensors:
                    self.sensors[sid].online = False

                continue

            # Gerät online
            dev.mark_online()
            data = result["data"]

            # Sensorwerte aktualisieren
            for s in data.get("sensors", []):
                sid = s["ID"]
                val = s["Val"]

                if sid in self.sensors:
                    sensor = self.sensors[sid]
                    sensor.online = True
                    sensor.last_online_ts = time.time()
                    sensor.update(val)

        self.storage.save(self.sensors)

    # ----------------------------------------------------------------------

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

    def print_all_sensor_settings(self):
        for sid, sensor in sorted(self.sensors.items()):
            print(f"\n=== {sid} ({sensor.name}) ===")
            settings = sensor.get_settings()
            # Dynamische Spaltenbreite
            max_key_len = max(len(k) for k in settings.keys())
            for key, value in settings.items():
                print(f"{key:<{max_key_len}} : {value}")

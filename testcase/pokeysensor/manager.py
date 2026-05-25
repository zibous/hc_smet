import time
import yaml
import os

from sensor import S0Sensor
from storage import StorageHandler
from network import NetworkClient
from pokeydevice import PoKeysDevice


class PoKeysManager:

    def __init__(self):
        self.devices = [
            PoKeysDevice("poKey64", "10.1.1.64", 1, 25),
            PoKeysDevice("poKey65", "10.1.1.65", 26, 50),
        ]

        self.network = NetworkClient()

        filename = os.path.splitext(os.path.basename(__file__))[0] + ".json"
        self.storage = StorageHandler(filename)

        self.sensors = {}
        self.letztes_update = "Noch keine Daten empfangen"

        # ---------------- YAML laden ----------------
        with open("house.yaml", encoding="utf-8") as f:
            cfg = yaml.safe_load(f)

        sensor_cfg = cfg["sensors"]

        # ---------------- Sensoren erzeugen ----------------
        for sid, data in sensor_cfg.items():
            sensor = S0Sensor(data["name"], data["impulse"])
            sensor.model = data["model"]
            sensor.id = sid
            sensor.room = data.get("room")
            sensor.devices = data.get("devices", [])
            self.sensors[sid] = sensor

        # ---------------- Interfaces zuordnen ----------------
        for sid, sensor in self.sensors.items():
            num = int(sid[1:])
            for dev in self.devices:
                if dev.start_id <= num <= dev.end_id:
                    dev.sensors.append(sid)
                    sensor.interface = dev.id
                    break

        # ---------------- Pins zuordnen ----------------
        self.pin_order = [
            0, 1, 4, 5, 8, 10, 14, 15, 18, 19,
            20, 21, 22, 23, 24, 25, 26, 27,
            40, 41, 42, 43, 45, 47, 48,
        ]

        for dev in self.devices:
            dev.sensors.sort()
            for index, sid in enumerate(dev.sensors):
                if index < len(self.pin_order):
                    self.sensors[sid].pin = self.pin_order[index]

        # ---------------- Persistente Daten laden ----------------
        self.storage.load(self.sensors)

    # ----------------------------------------------------------------------

    def update_sensors(self):
        self.letztes_update = time.strftime("%Y-%m-%d %H:%M:%S")

        for dev in self.devices:
            try:
                result = self.network.fetch(dev.ip)
            except Exception:
                dev.mark_offline()
                for sid in dev.sensors:
                    self.sensors[sid].online = False
                continue

            if not result.get("online", False):
                dev.mark_offline()
                for sid in dev.sensors:
                    self.sensors[sid].online = False
                continue

            dev.mark_online()
            data = result.get("data", {})

            for s in data.get("sensors", []):
                sid = s.get("ID")
                val = s.get("Val")

                if sid not in self.sensors:
                    continue

                sensor = self.sensors[sid]
                sensor.online = True
                sensor.last_online_ts = time.time()

                try:
                    sensor.update(float(val))
                except Exception:
                    continue

        # Persistenz
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

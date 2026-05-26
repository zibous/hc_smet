import time
import yaml
import os
import sys
from pathlib import Path
import logging

from sensor import S0Sensor
from storage import StorageHandler
from network import NetworkClient
from pokeydevice import PoKeysDevice

# Projektwurzel ermitteln
ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT))

from app.core.app_config import settings
logger = logging.getLogger(__name__)

def parse_range(text: str) -> tuple[int, int]:
    start, end = map(int, text.split("-"))
    return start, end

class PoKeysManager:

    def __init__(self):

        self.settings = settings
        self.devices = []   # ← WICHTIG: immer definieren!
        self._load_devices()
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
            int(pin.strip())
            for pin in settings.POKEYS_DEVICE2_PINS.split(",")
        ]

        for dev in self.devices:
            dev.sensors.sort()
            for index, sid in enumerate(dev.sensors):
                if index < len(self.pin_order):
                    self.sensors[sid].pin = self.pin_order[index]

        # ---------------- Persistente Daten laden ----------------
        self.storage.load(self.sensors)


    # ----------------------------------------------------------------------

    def _load_devices(self):
        idx = 1
        while hasattr(self.settings, f"POKEYS_DEVICE{idx}_NAME"):
            name = getattr(self.settings, f"POKEYS_DEVICE{idx}_NAME")
            ip   = getattr(self.settings, f"POKEYS_DEVICE{idx}_IP")
            rng  = getattr(self.settings, f"POKEYS_DEVICE{idx}_SENSORS")
            start, end = map(int, rng.split("-"))
            logger.info(f"Device {name}, {ip} ready")
            self.devices.append(
                PoKeysDevice(name, ip, start, end)
            )
            idx += 1


    def update_sensors(self):
        self.letztes_update = time.strftime("%Y-%m-%d %H:%M:%S")

        for dev in self.devices:
            try:
                result = self.network.fetch(dev.ip)
                logger.info(f"Loaded device data von: {dev.ip}, Ergebnisse neu geladen.")

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
                    # Neue Daten übertragen an sensor
                    logger.debug(f"Update des Sensors {sid} mit neuen Werten")
                    sensor.update(float(val))

                except Exception:
                    logger.error(f"Fehler beim Update des Sensors {sid}")
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

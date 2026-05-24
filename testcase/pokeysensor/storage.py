# storage.py
import json

class StorageHandler:
    def __init__(self, filename):

        self.filename = filename

    def load(self, sensors):
        try:
            with open(self.filename, "r") as f:
                data = json.load(f)
            for name, sensor in sensors.items():
                if name in data:
                    sensor.load_dict(data[name])
        except:
            pass

    def save(self, sensors):
        with open(self.filename, "w") as f:
            json.dump({n: s.to_dict() for n, s in sensors.items()}, f, indent=2)

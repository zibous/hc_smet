# sensor.py
import time

class MovingAverage:
    def __init__(self, size=5):
        self.size = size
        self.values = []

    def add(self, value):
        self.values.append(value)
        if len(self.values) > self.size:
            self.values.pop(0)

    def avg(self):
        if not self.values:
            return 0
        return sum(self.values) / len(self.values)


class S0Sensor:
    def __init__(self, name, impulse):

        self.name = name
        self.impulse = impulse
        self.faktor = 100 / impulse

        self.model = None
        self.room = None
        self.devices = []

        self.total_kwh = 0.0
        self.prev_kwh = 0.0
        self.verbrauch_kwh = 0.0
        self.watt = 0
        self.last_ts = time.time()
        self.initialized = False

        # Zusatzwerte
        self.kosten = 0.0
        self.co2 = 0.0
        self.kwh_pro_stunde = 0.0
        self.prognose_tag = 0.0
        self.prognose_jahr = 0.0
        self.sekunden_pro_impuls = 0.0

        self.online = False
        self.status = ""
        self.last_online_ts = 0

        self.watt_ma = MovingAverage(size=5)

    def update(self, raw_val):
        now = time.time()
        new_kwh = round(raw_val * self.faktor, 6)

        if not self.initialized:
            self.total_kwh = new_kwh
            self.prev_kwh = new_kwh
            self.last_ts = now
            self.initialized = True
            return

        dt = max(now - self.last_ts, 1)
        diff = round(new_kwh - self.total_kwh, 6)

        self.prev_kwh = self.total_kwh
        self.total_kwh = new_kwh

        self.verbrauch_kwh = diff if diff > 0 else 0.0
        self.watt = int((diff * 3600000) / dt) if diff > 0 else 0

        self.calcdata(dt)
        self.last_ts = now

    # Region	CO₂‑Faktor
    # Österreich (UBA)	300–350 g/kWh
    # Deutschland (UBA)	350–450 g/kWh
    # EU‑Durchschnitt	250–400 g/kWh

    # TODO: co2 nicht hardcored - aus app_config.py laden !!!
    # TODO: preis nicht hardcored - aus app_config.py laden !!!

    def calcdata(self, dt):

        preis = 0.24
        co2 = 380.0
        # Kosten & CO2
        self.kosten = round(self.verbrauch_kwh * preis, 6)
        self.co2 = round(self.verbrauch_kwh * co2, 6)

        # Verbrauch pro Stunde (über echte Zeit verteilt)
        stundenfaktor = 3600 / dt
        self.kwh_pro_stunde = self.verbrauch_kwh * stundenfaktor

        # Watt aus kWh/h
        self.watt = int(self.kwh_pro_stunde * 1000)

        # Moving Average anwenden
        self.watt_ma.add(self.watt)
        self.watt = int(self.watt_ma.avg())

        # Prognosen
        self.prognose_tag = round(self.kwh_pro_stunde * 24 * preis, 2)
        self.prognose_jahr = round(self.kwh_pro_stunde * 8760 * preis, 2)

        # Sekunden pro Impuls (nur wenn Leistung > 0)
        if self.watt > 0:
            kw = self.watt / 1000
            self.sekunden_pro_impuls = round(3600 / (kw * self.impulse), 2)
        else:
            self.sekunden_pro_impuls = 0

    def calcdata(self, dt):

        # TODO: nicht hardcored - aus app_config.py laden !!!
        preis = 0.24

        co2 = 380.0

        self.kosten = round(self.verbrauch_kwh * preis, 6)
        self.co2 = round(self.verbrauch_kwh * co2, 6)

        stundenfaktor = 3600 / dt
        self.kwh_pro_stunde = self.verbrauch_kwh * stundenfaktor

        self.watt = int(self.kwh_pro_stunde * 1000)

        self.prognose_tag = round(self.kwh_pro_stunde * 24 * preis, 2)
        self.prognose_jahr = round(self.kwh_pro_stunde * 8760 * preis, 2)

        if self.watt > 0:
            kw = self.watt / 1000
            self.sekunden_pro_impuls = round(3600 / (kw * self.impulse), 2)
        else:
            self.sekunden_pro_impuls = 0

    def to_dict(self):
        return {
            "name": self.name,
            "model": self.model,
            "room": self.room,
            "devices": self.devices,
            "total_kwh": self.total_kwh,
            "kwh": self.verbrauch_kwh,
            "watt": self.watt,
            "kosten": self.kosten,
            "co2": self.co2,
            "trend_kwh_h": self.kwh_pro_stunde,
            "prognose_tag": self.prognose_tag,
            "prognose_jahr": self.prognose_jahr,
            "sekunden_pro_impuls": self.sekunden_pro_impuls,
            "faktor": self.faktor,
            "ts": self.last_ts,
            "online": self.online,
            "last_online_ts": self.last_online_ts
        }

    def load_dict(self, data):
        self.total_kwh = data["kwh"]
        self.prev_kwh = data["kwh"]
        self.watt = data["watt"]
        self.last_ts = data["ts"]
        self.initialized = True

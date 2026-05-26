import time
import sys
from pathlib import Path

# Projektwurzel ermitteln
ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT))

from app.core.app_config import settings

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

        self.interface = ""
        self.pin = 0

        self.model = None
        self.room = None
        self.devices = []

        # Messwerte
        self.total_kwh = 0.0
        self.prev_kwh = 0.0
        self.verbrauch_kwh = 0.0
        self.watt = 0
        self.last_ts = time.time()
        self.initialized = False

        # Zusatzwerte
        self.kosten = 0.0
        self.co2 = 0
        self.kwh_pro_stunde = 0.0
        self.prognose_tag = 0.0
        self.prognose_jahr = 0.0
        self.sekunden_pro_impuls = 0.0
        self.energieklasse = "A"

        # Status
        self.online = False
        self.last_online_ts = 0
        self.update_ts = 0

        self.watt_ma = MovingAverage(size=5)

    # --------------------------------------------------------------

    def update(self, raw_val: float):
        now = time.time()
        new_kwh = round(raw_val * self.faktor, 6)

        # Erstes Update (nur wenn KEINE JSON-Daten geladen wurden)
        if not self.initialized:
            self.total_kwh = new_kwh
            self.prev_kwh = new_kwh
            self.last_ts = now
            self.initialized = True
            return

        dt = max(now - self.last_ts, 1)

        # --- FÄNGT DAS LOGISCHE HOCHSCHIESSEN DER WERTE ZU 100% AB ---
        if new_kwh < self.total_kwh:
            # Das Interface hat einen Reset durchgeführt oder liefert ungültige 0-Werte.
            # Da S0-Zähler niemals rückwärts laufen können, ignorieren wir das Delta
            # und setzen die Basis lautlos auf den neuen Nullpunkt des PoKeys zurück.
            self.total_kwh = new_kwh
            self.prev_kwh = new_kwh
            self.verbrauch_kwh = 0.0
            self.last_ts = now
            return  # Fehlerhaften Durchlauf abbrechen - schützt Ihre historischen Berechnungen

        diff = round(new_kwh - self.total_kwh, 6)

        # --- SPIKE-SCHUTZ GEGEN SIGNALRAUSCHEN (KORRIGIERTER GRENZWERT FÜR IHREN FAKTOR) ---
        # Angepasst auf Ihre Faktor-Skalierung, um Fehlalarme bei normalen Impulsen zu verhindern.
        max_erlaubte_kwh_pro_sekunde = 2.0
        if dt > 0 and (diff / dt) > max_erlaubte_kwh_pro_sekunde:
            # Wir korrigieren total_kwh lautlos auf den neuen Wert, verwerfen aber das diff!
            self.prev_kwh = self.total_kwh
            self.total_kwh = new_kwh
            self.verbrauch_kwh = 0.0
            self.last_ts = now
            return  # Fehlerhaften Störimpuls-Durchlauf abbrechen!

        self.prev_kwh = self.total_kwh
        self.total_kwh = new_kwh

        self.verbrauch_kwh = diff if diff > 0 else 0.0

        if self.verbrauch_kwh > 0:
            self.update_ts = now

        self.calcdata(dt)
        self.last_ts = now

    # --------------------------------------------------------------
    def calcdata(self, dt: float):

        preis = list(settings.STROMPREISE.values())[-1]


        ## TODO: prüfen im json speichern, da sonst bei eine
        ## restart der Anendung das nicht stimmt.

        # --- 1. Laufzeit-Erfassung für die Langzeit-Prognose (KORRIGIERT GEGEN SPEICHER-ERASURE) ---
        if not hasattr(self, 'gesamte_laufzeit_sekunden'):
            self.gesamte_laufzeit_sekunden = 0.0

            # Schützt geladene Daten: Nur auf 0 setzen, wenn noch kein Wert aus dem JSON da ist
            if not hasattr(self, 'gesamter_historischer_verbrauch'):
                self.gesamter_historischer_verbrauch = 0.0

        self.gesamte_laufzeit_sekunden += dt

        # Wichtig: Sie müssen den übergeordneten, fortlaufenden Gesamtverbrauch
        # (z. B. s.verbrauch_kwh aus der sensorList.json) hier aufsummieren oder übergeben,
        # falls self.verbrauch_kwh in dieser Methode nur das Delta des aktuellen Intervalls ist!
        # Wenn self.verbrauch_kwh bereits der kumulierte Gesamtzählerstand ist,
        # nutzen Sie stattdessen: self.gesamter_historischer_verbrauch = self.verbrauch_kwh
        self.gesamter_historischer_verbrauch += self.verbrauch_kwh

        # --- 2. Aktuelle Momentanleistung (Watt) berechnen ---
        stundenfaktor = 3600 / dt
        self.kwh_pro_stunde = self.verbrauch_kwh * stundenfaktor

        # Rohwert in Watt
        self.watt = int(self.kwh_pro_stunde * 1000)

        # Gleitender Mittelwert (Moving Average), um Spitzen bei getakteten Geräten zu glätten
        self.watt_ma.add(self.watt)
        self.watt = int(self.watt_ma.avg())

        # --- 3. Aktuelle IST-Kosten und CO2 (Basierend auf dem bisherigen Gesamtverbrauch) ---
        self.kosten = round(self.gesamter_historischer_verbrauch * preis, 6)
        self.co2 = round(self.gesamter_historischer_verbrauch * settings.CO2_WERT, 6)

        # --- 4. KORRIGIERTE PROGNOSE (Historischer Durchschnitt statt Momentanwert) ---
        # Wir berechnen, wie viel das Gerät seit Messbeginn im Schnitt PRO STUNDE verbraucht hat (inkl. Pausen)
        if self.gesamte_laufzeit_sekunden > 0:
            stunden_seit_start = self.gesamte_laufzeit_sekunden / 3600.0
            echter_historischer_schnitt_pro_stunde = self.gesamter_historischer_verbrauch / stunden_seit_start
        else:
            echter_historischer_schnitt_pro_stunde = 0.0

        # Die Prognose nutzt nun den geglätteten Langzeit-Durchschnittswert
        self.prognose_tag = round(echter_historischer_schnitt_pro_stunde * 24 * preis, 2)
        self.prognose_jahr = round(echter_historischer_schnitt_pro_stunde * 8760 * preis, 2)

        # --- 5. S0-Impuls-Zeitabstand berechnen ---
        if self.watt > 0:
            kw = self.watt / 1000
            # s.impulse muss die Zählerkonstante sein (z.B. 1000 oder 800)
            self.sekunden_pro_impuls = round(3600 / (kw * self.impulse), 2)
        else:
            self.sekunden_pro_impuls = 0

        # --- 6. ERWEITERT: Energieklasse aus der stabilen Jahresprognose ableiten ---
        jahr_kwh = echter_historischer_schnitt_pro_stunde * 8760

        if jahr_kwh < settings.LIMIT_CLASS_A:
            self.energieklasse = "A"
        elif jahr_kwh < settings.LIMIT_CLASS_B:
            self.energieklasse = "B"
        elif jahr_kwh < settings.LIMIT_CLASS_C:
            self.energieklasse = "C"
        elif jahr_kwh < settings.LIMIT_CLASS_D:
            self.energieklasse = "D"
        elif jahr_kwh < settings.LIMIT_CLASS_E:
            self.energieklasse = "E"
        elif jahr_kwh < settings.LIMIT_CLASS_F:
            self.energieklasse = "F"
        else:
            self.energieklasse = "G"

    # --------------------------------------------------------------

    def to_dict(self):
        # Variante C: vollständige Messwerte, KEINE Konfiguration
        return {
            "total_kwh": self.total_kwh,
            "verbrauch_kwh": self.verbrauch_kwh,
            "watt": self.watt,
            "kwh_pro_stunde": self.kwh_pro_stunde,
            "kosten": self.kosten,
            "co2": self.co2,
            "prognose_tag": self.prognose_tag,
            "prognose_jahr": self.prognose_jahr,
            "sekunden_pro_impuls": self.sekunden_pro_impuls,
            "energieklasse": self.energieklasse,
            "gesamte_laufzeit_sekunden": getattr(self, 'gesamte_laufzeit_sekunden', 0.0),
            "gesamter_historischer_verbrauch": getattr(self, 'gesamter_historischer_verbrauch', 0.0),
            "last_online_ts": self.last_online_ts,
            "online": self.online,
            "ts": self.last_ts,
        }

    # --------------------------------------------------------------

    def load_dict(self, data: dict):
        self.total_kwh = data.get("total_kwh", self.total_kwh)
        self.prev_kwh = self.total_kwh

        self.verbrauch_kwh = data.get("verbrauch_kwh", 0.0)
        self.watt = data.get("watt", 0)
        self.kwh_pro_stunde = data.get("kwh_pro_stunde", 0.0)

        self.kosten = data.get("kosten", 0.0)
        self.co2 = data.get("co2", 0.0)
        self.prognose_tag = data.get("prognose_tag", 0.0)
        self.prognose_jahr = data.get("prognose_jahr", 0.0)
        self.sekunden_pro_impuls = data.get("sekunden_pro_impuls", 0.0)
        self.energieklasse = data.get("energieklasse", "A")

        # Historische Laufzeiten wiederherstellen
        self.gesamte_laufzeit_sekunden = data.get("gesamte_laufzeit_sekunden", 0.0)
        self.gesamter_historischer_verbrauch = data.get("gesamter_historischer_verbrauch", 0.0)

        self.last_ts = data.get("ts", time.time())
        self.last_online_ts = data.get("last_online_ts", 0)
        self.online = data.get("online", False)

        self.initialized = True

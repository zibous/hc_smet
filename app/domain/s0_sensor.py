# -*- coding: utf-8 -*-
"""S0Sensor — Repräsentation eines einzelnen S0-Energiezählers.

Berechnet Watt, kWh, Kosten, CO₂, Prognosen und Energieklasse.
Enthält dreifachen Spike-Schutz gegen Appausfall-Hochschießen.
"""

import time
import logging

from app.core.app_config import settings

logger = logging.getLogger(__name__)


class MovingAverage:
    """Gleitender Durchschnitt für Watt-Glättung."""

    def __init__(self, size: int = 5):
        self.size = size
        self.values: list[float] = []

    def add(self, value: float):
        self.values.append(value)
        if len(self.values) > self.size:
            self.values.pop(0)

    def avg(self) -> float:
        if not self.values:
            return 0
        return sum(self.values) / len(self.values)


class S0Sensor:
    """S0-Impulszähler mit Verbrauchsberechnung und Spike-Schutz.

    100% SCHUTZ VOR APPAUSFALL-HOCHSCHIESSEN:
    1. Zähler-Reset-Erkennung (new_kwh < total_kwh)
    2. Spike-Schutz (max kWh/s Limit)
    3. Moving Average für Watt-Glättung
    """

    def __init__(self, name: str, impulse: int):
        self.name = name
        self.impulse = impulse
        self.faktor = 100 / impulse

        self.interface = ""
        self.pin = 0
        self.id = ""

        self.model: str | None = None
        self.room: str | None = None
        self.devices: list[str] = []

        # Messwerte
        self.total_kwh = 0.0
        self.prev_kwh = 0.0
        self.verbrauch_kwh = 0.0
        self.watt = 0
        self.last_ts = time.time()
        self.initialized = False

        # Zusatzwerte (berechnet)
        self.kosten = 0.0
        self.co2 = 0.0
        self.kwh_pro_stunde = 0.0
        self.prognose_tag = 0.0
        self.prognose_jahr = 0.0
        self.sekunden_pro_impuls = 0.0
        self.energieklasse = "A"

        # Status
        self.online = False
        self.last_online_ts = 0
        self.update_ts = 0

        # Glättung
        self.watt_ma = MovingAverage(size=5)
        self.has_ever_pulsed = False

        # Historische Akkumulatoren
        self.gesamte_laufzeit_sekunden = 0.0
        self.gesamter_historischer_verbrauch = 0.0

    # ------------------------------------------------------------------
    # UPDATE — Kernlogik mit Spike-Schutz
    # ------------------------------------------------------------------

    def update(self, raw_val: float):
        """Verarbeitet einen neuen Rohwert vom PoKeys-Interface.

        Enthält dreifachen Schutz gegen Hochschießen:
        1. Zähler-Reset: new_kwh < total_kwh → Reset ohne Sprung
        2. Spike: Absurde Änderungsrate → ignorieren
        3. Moving Average: Glättet Watt-Werte
        """
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

        # --- SCHUTZ 1: Zähler-Reset-Erkennung (PoKeys-Neustart) ---
        if new_kwh < self.total_kwh:
            self.total_kwh = new_kwh
            self.prev_kwh = new_kwh
            self.verbrauch_kwh = 0.0
            self.last_ts = now
            return

        diff = round(new_kwh - self.total_kwh, 6)

        # --- SCHUTZ 2: Spike-Schutz (max 2 kWh/s = 7200 kW) ---
        max_erlaubte_kwh_pro_sekunde = 2.0
        if dt > 0 and (diff / dt) > max_erlaubte_kwh_pro_sekunde:
            logger.warning(
                f"[SPIKE-SCHUTZ] {self.id}: {diff:.4f} kWh in {dt:.0f}s blockiert"
            )
            self.prev_kwh = self.total_kwh
            self.total_kwh = new_kwh
            self.verbrauch_kwh = 0.0
            self.last_ts = now
            return

        self.prev_kwh = self.total_kwh
        self.total_kwh = new_kwh

        self.verbrauch_kwh = diff if diff > 0 else 0.0

        if self.verbrauch_kwh > 0:
            self.update_ts = now

        # Flag: Sensor hat jemals Impulse gehabt
        if self.total_kwh > 0:
            self.has_ever_pulsed = True

        self._calcdata(dt)
        self.last_ts = now

    # ------------------------------------------------------------------
    # BERECHNUNG — Kosten, CO₂, Prognosen, Energieklasse
    # ------------------------------------------------------------------

    def _calcdata(self, dt: float):
        """Berechnet abgeleitete Werte aus dem aktuellen Verbrauch.

        Watt und kWh/h werden live berechnet.
        Prognosen (Tag/Jahr), Energieklasse und CO₂ kommen aus der
        Analytics-DB (wird nachts berechnet). Falls keine Analytics-Daten
        vorhanden sind, wird ein einfacher Fallback verwendet.
        """
        preis = list(settings.STROMPREISE.values())[-1]

        self.gesamte_laufzeit_sekunden += dt
        self.gesamter_historischer_verbrauch += self.verbrauch_kwh

        stundenfaktor = 3600 / dt
        self.kwh_pro_stunde = self.verbrauch_kwh * stundenfaktor

        self.watt = int(self.kwh_pro_stunde * 1000)
        self.watt_ma.add(self.watt)
        self.watt = int(self.watt_ma.avg())

        self.kosten = round(self.gesamter_historischer_verbrauch * preis, 6)
        self.co2 = round(self.gesamter_historischer_verbrauch * settings.CO2_WERT, 6)

        if self.watt > 0:
            kw = self.watt / 1000
            self.sekunden_pro_impuls = round(3600 / (kw * self.impulse), 2)
        else:
            self.sekunden_pro_impuls = 0

        # Prognosen und Energieklasse werden NICHT live berechnet.
        # Sie werden beim Start aus der Analytics-DB geladen (load_prognosis).
        # Fallback: Wenn keine Analytics-Daten vorhanden, einfache Hochrechnung
        if not hasattr(self, '_prognosis_loaded') or not self._prognosis_loaded:
            if self.gesamte_laufzeit_sekunden > 3600:
                stunden = self.gesamte_laufzeit_sekunden / 3600.0
                schnitt = self.gesamter_historischer_verbrauch / stunden
                self.prognose_tag = round(schnitt * 24 * preis, 2)
                self.prognose_jahr = round(schnitt * 8760 * preis, 2)
                jahr_kwh = schnitt * 8760
                self._set_energieklasse(jahr_kwh)

    def _set_energieklasse(self, jahr_kwh: float):
        """Setzt die Energieklasse basierend auf dem Jahresverbrauch."""
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

    def load_prognosis(self, row: dict):
        """Lädt Prognose-Werte aus der Analytics-DB (sensor_prognosis Tabelle).

        Wird beim App-Start vom PoKeysManager aufgerufen.
        """
        self.prognose_tag = round(row.get("avg_kwh_per_day", 0) * list(settings.STROMPREISE.values())[-1], 2)
        self.prognose_jahr = row.get("prognose_jahr_eur", 0.0)
        self.energieklasse = row.get("energieklasse", "A")
        self._prognosis_loaded = True

    # ------------------------------------------------------------------
    # SERIALISIERUNG
    # ------------------------------------------------------------------

    def to_dict(self) -> dict:
        """Serialisiert den Sensor-State für JSON-Persistenz."""
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
            "gesamte_laufzeit_sekunden": self.gesamte_laufzeit_sekunden,
            "gesamter_historischer_verbrauch": self.gesamter_historischer_verbrauch,
            "last_online_ts": self.last_online_ts,
            "online": self.online,
            "ts": self.last_ts,
            "has_ever_pulsed": self.has_ever_pulsed,
        }

    def load_dict(self, data: dict):
        """Lädt den Sensor-State aus JSON-Persistenz."""
        self.total_kwh = data.get("total_kwh", self.total_kwh)
        self.prev_kwh = data.get("total_kwh", self.prev_kwh)
        self.verbrauch_kwh = data.get("verbrauch_kwh", 0.0)
        self.watt = data.get("watt", 0)
        self.kwh_pro_stunde = data.get("kwh_pro_stunde", 0.0)
        self.kosten = data.get("kosten", 0.0)
        self.co2 = data.get("co2", 0.0)
        self.prognose_tag = data.get("prognose_tag", 0.0)
        self.prognose_jahr = data.get("prognose_jahr", 0.0)
        self.sekunden_pro_impuls = data.get("sekunden_pro_impuls", 0.0)
        self.energieklasse = data.get("energieklasse", "A")
        self.gesamte_laufzeit_sekunden = data.get("gesamte_laufzeit_sekunden", 0.0)
        self.gesamter_historischer_verbrauch = data.get("gesamter_historischer_verbrauch", 0.0)
        self.last_online_ts = data.get("last_online_ts", 0)
        self.online = data.get("online", False)
        self.last_ts = data.get("ts", time.time())
        self.has_ever_pulsed = data.get("has_ever_pulsed", False)
        self.initialized = True

# -*- coding: utf-8 -*-
"""Webhook-Schemas für hc_smet – Verbrauch Haus mit Geschoss-Attributen."""

from pydantic import BaseModel
from typing import Dict


class HeartbeatKPI(BaseModel):
    """KPI-Daten im Heartbeat (alle 60s).

    Hauptwert: Tagesverbrauch Haus (kWh)
    Attribute: Verbrauch pro Geschoss heute
    """
    haus_today_kwh: float = 0.0
    eg_today_kwh: float = 0.0       # Kellergeschoss
    wg_today_kwh: float = 0.0       # Wohngeschoss
    og_today_kwh: float = 0.0       # Obergeschoss
    dg_today_kwh: float = 0.0       # Dachgeschoss
    os_today_kwh: float = 0.0       # Außenbereich
    devices_online: int = 0
    devices_total: int = 2
    sensors_active: int = 0


class DailySummary(BaseModel):
    """Zusammenfassung bei Tageswechsel – Verbrauch pro Geschoss."""
    haus_kwh: float = 0.0
    eg_kwh: float = 0.0
    wg_kwh: float = 0.0
    og_kwh: float = 0.0
    dg_kwh: float = 0.0
    os_kwh: float = 0.0


class MonthlySummary(BaseModel):
    """Zusammenfassung bei Monatswechsel – Verbrauch pro Geschoss."""
    haus_kwh: float = 0.0
    eg_kwh: float = 0.0
    wg_kwh: float = 0.0
    og_kwh: float = 0.0
    dg_kwh: float = 0.0
    os_kwh: float = 0.0

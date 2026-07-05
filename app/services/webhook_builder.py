# -*- coding: utf-8 -*-
"""Webhook KPI Builder für hc_smet.

Stellt die Callbacks für den WebhookPublisher bereit:
- build_heartbeat() → Haus-Verbrauch + Geschosse
- build_daily() → Tageswerte
- build_monthly() → Monatswerte
"""

from datetime import datetime, timezone

from app.infrastructure.database.dbconnect import Database
import app.domain.house as house
from app.schemas.webhook_data import HeartbeatKPI, DailySummary, MonthlySummary

STRUCTURE = house.STRUCTURE


def _get_day_consumption(sensor_id: str, start_ts: int = 0) -> float:
    """Tagesverbrauch eines Sensors aus hourly_values."""
    if Database._instance is None:
        return 0.0
    if start_ts == 0:
        start_ts = int(datetime.now(timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        ).timestamp())
    try:
        year = datetime.now().year
        conn = Database._instance.get_conn(year=year)
        row = conn.execute(
            "SELECT COALESCE(SUM(consumption), 0) FROM hourly_values WHERE sensor_id = ? AND hour >= ?",
            (sensor_id, start_ts)
        ).fetchone()
        conn.close()
        return float(row[0]) if row else 0.0
    except Exception:
        return 0.0


def _get_area_kwh(area_id: str, start_ts: int = 0) -> float:
    """Tagesverbrauch für ein Geschoss (Area)."""
    rooms_info = STRUCTURE.get("rooms", {})
    sensors_info = STRUCTURE.get("sensors", {})
    room_ids = [rid for rid, r in rooms_info.items() if r.get("area") == area_id]
    sensor_ids = [sid for sid, s in sensors_info.items() if s.get("room") in room_ids]
    return round(sum(_get_day_consumption(sid, start_ts) for sid in sensor_ids), 3)


def build_heartbeat(pokeys_manager=None) -> HeartbeatKPI:
    """Baut HeartbeatKPI mit Haus- und Geschoss-Verbrauch."""
    sensors_info = STRUCTURE.get("sensors", {})
    haus_kwh = round(sum(_get_day_consumption(sid) for sid in sensors_info.keys()), 3)

    devices_online = 0
    sensors_active = 0
    if pokeys_manager:
        for dev in pokeys_manager.devices:
            if dev.online:
                devices_online += 1
        sensors_active = sum(1 for s in pokeys_manager.sensors.values() if s.online)

    return HeartbeatKPI(
        haus_today_kwh=haus_kwh,
        eg_today_kwh=_get_area_kwh("EG"),
        wg_today_kwh=_get_area_kwh("WG"),
        og_today_kwh=_get_area_kwh("OG"),
        dg_today_kwh=_get_area_kwh("DG"),
        os_today_kwh=_get_area_kwh("OS"),
        devices_online=devices_online,
        devices_total=2,
        sensors_active=sensors_active,
    )


def build_daily() -> DailySummary:
    """Baut DailySummary bei Tageswechsel."""
    sensors_info = STRUCTURE.get("sensors", {})
    return DailySummary(
        haus_kwh=round(sum(_get_day_consumption(sid) for sid in sensors_info.keys()), 3),
        eg_kwh=_get_area_kwh("EG"),
        wg_kwh=_get_area_kwh("WG"),
        og_kwh=_get_area_kwh("OG"),
        dg_kwh=_get_area_kwh("DG"),
        os_kwh=_get_area_kwh("OS"),
    )


def build_monthly() -> MonthlySummary:
    """Baut MonthlySummary bei Monatswechsel."""
    first_of_month = datetime.now(timezone.utc).replace(
        day=1, hour=0, minute=0, second=0, microsecond=0
    )
    month_start_ts = int(first_of_month.timestamp())
    sensors_info = STRUCTURE.get("sensors", {})

    haus = round(sum(_get_day_consumption(sid, month_start_ts) for sid in sensors_info.keys()), 3)
    return MonthlySummary(
        haus_kwh=haus,
        eg_kwh=_get_area_kwh("EG", month_start_ts),
        wg_kwh=_get_area_kwh("WG", month_start_ts),
        og_kwh=_get_area_kwh("OG", month_start_ts),
        dg_kwh=_get_area_kwh("DG", month_start_ts),
        os_kwh=_get_area_kwh("OS", month_start_ts),
    )

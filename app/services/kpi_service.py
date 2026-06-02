# app/services/kpi_service.py
"""KPI-Service für hc_smet – liefert Smartmeter-Übersichtsdaten für das zentrale Dashboard."""

import logging
import time
from datetime import datetime

from app.core.app_config import settings
from app.infrastructure.database.dbconnect import Database
from app.schemas.kpi import KpiHero, KpiIndicator, KpiResponse

logger = logging.getLogger(__name__)


class KpiService:
    """Aggregiert Strom-KPI-Daten aus Live-Sensoren und hourly_values."""

    def get_kpis(self) -> KpiResponse:
        now = datetime.now()

        # Live-Daten: Gesamtleistung (Watt) und aktive Sensoren
        total_watt = 0
        active_sensors = 0

        if settings.POKEY_SERVICE.upper() == "GET":
            try:
                import app.main as main_module
                app_state = getattr(getattr(main_module, "app", None), "state", None)
                manager = getattr(app_state, "pokeys_manager", None) if app_state else None
                if manager:
                    all_data = manager.get_all_data()
                    for info in all_data.values():
                        watt = info.get("watt", 0) or 0
                        if watt > 0:
                            total_watt += watt
                            active_sensors += 1
            except Exception as e:
                logger.warning(f"KPI: PoKeysManager nicht verfügbar: {e}")
        else:
            try:
                from app.api.parsdecoder import _shared_store
                store_data = _shared_store.get_all()
                active_sensors = len([s for s in store_data.values() if s.current > 0])
            except Exception as e:
                logger.warning(f"KPI: SensorStore nicht verfügbar: {e}")

        # Tagesverbrauch aus hourly_values
        today_kwh = 0.0
        sparkline = []
        try:
            if Database._instance:
                now_ts = int(time.time())
                today_start = int(datetime(now.year, now.month, now.day).timestamp())
                # Letzte 24h für Sparkline
                cutoff_24h = now_ts - 24 * 3600
                cutoff_hour = (cutoff_24h // 3600) * 3600

                conn = Database._instance.get_conn()
                try:
                    # Tagesverbrauch
                    row = conn.execute("""
                        SELECT COALESCE(SUM(consumption), 0) as total
                        FROM hourly_values
                        WHERE hour >= ?
                    """, (today_start,)).fetchone()
                    today_kwh = round(row[0], 2) if row else 0.0

                    # Sparkline: Stundenwerte der letzten 24h
                    rows = conn.execute("""
                        SELECT hour, SUM(consumption) as total
                        FROM hourly_values
                        WHERE hour >= ?
                        GROUP BY hour
                        ORDER BY hour ASC
                    """, (cutoff_hour,)).fetchall()
                    sparkline = [round(r[1], 2) for r in rows if r[1]]
                finally:
                    conn.close()
        except Exception as e:
            logger.warning(f"KPI: DB-Abfrage fehlgeschlagen: {e}")

        # Status
        status = "ok" if active_sensors > 0 or today_kwh > 0 else "warning"

        # Label
        label_parts = []
        if total_watt > 0:
            label_parts.append(f"Aktuell {total_watt} W")
        label_parts.append(f"{active_sensors} Sensoren aktiv")
        label = " · ".join(label_parts)

        return KpiResponse(
            app_id=settings.KPI_APP_ID,
            app_name=settings.KPI_APP_NAME,
            icon=settings.KPI_ICON,
            url=settings.KPI_URL,
            status=status,
            ts=now.isoformat(timespec="seconds"),
            hero=KpiHero(
                value=today_kwh if today_kwh > 0 else total_watt,
                unit="kWh" if today_kwh > 0 else "W",
                label=label,
            ),
            detail=f"Heute {now.strftime('%d.%m.%Y')}",
            indicator=KpiIndicator(
                type="sparkline",
                values=sparkline,
            ) if sparkline else None,
        )

from datetime import datetime, timedelta
from fastapi import HTTPException
from app.services.dashboard_service import DashboardService
from app.infrastructure.builders.data_builder import (
    get_children,
    build_kpis,
    build_cards,
    build_timeseries,
)

class DashboardResponseBuilder:
    def __init__(self, node: str, service: DashboardService):
        self.node = node
        self.service = service
        self.start: datetime | None = None
        self.end: datetime | None = None
        self.period: str = "range"

        self.current_data = None
        # NEU: Speicher für die historischen Vergleichsdaten
        self.compare_data = None

    def parse_and_validate_time(self, from_ts: str, to_ts: str) -> "DashboardResponseBuilder":
        try:
            self.start = datetime.fromisoformat(from_ts)
            self.end = datetime.fromisoformat(to_ts)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid datetime format")

        if self.end <= self.start:
            raise HTTPException(status_code=400, detail="'to' must be after 'from'")

        self.period = "today" if (self.end - self.start) < timedelta(days=1) else "range"
        return self

    def fetch_data(self, freq: str = "1h") -> "DashboardResponseBuilder":
        if not self.start or not self.end:
            raise ValueError("Time range must be parsed before fetching data")

        self.current_data = self.service.get_current(self.node, self.start, self.end, freq)
        return self

    # =================================================================
    # NEU: Die Methode für den historischen Vergleichszeitraum
    # =================================================================
    def fetch_comparison_data(self, compare: int = 1, freq: str = "1h") -> "DashboardResponseBuilder":
        if not self.start or not self.end:
            raise ValueError("Time range must be parsed before fetching comparison data")

        # Wenn compare = 0 (deaktiviert), überspringen wir den DB-Abruf
        if compare <= 0:
            return self

        # Wir berechnen die Dauer des aktuellen Zeitraums
        duration = self.end - self.start

        # Verschiebung berechnen: Wir gehen genau um die Dauer der Spanne in die Vergangenheit
        # Bei compare=1 ist es die direkte Vorperiode, bei compare=2 die vorletzte usw.
        compare_start = self.start - (duration * compare)
        compare_end = self.end - (duration * compare)

        # Historische Daten aus der Datenbank laden
        self.compare_data = self.service.get_current(self.node, compare_start, compare_end, freq)
        return self

    def build(self) -> dict:
        return {
            "house": {
                "id": self.node,
                "name": "Haus",
                "children": get_children(self.node),
            },
            "kpis": build_kpis(self.current_data, self.compare_data, self.period),

            # ✨ HIER KORRIGIERT: self.compare_data als 4. Argument übergeben
            "cards": build_cards(self.node, self.current_data, self.period, self.compare_data),

            "timeseries": build_timeseries(self.current_data, self.compare_data, self.period, self.node),
        }


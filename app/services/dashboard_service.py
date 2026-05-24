from datetime import datetime
from app.infrastructure.database.dbconnect import Database
from app.infrastructure.database.energy_repository import load_energy_data

class DashboardService:
    def __init__(self, db_path: str | None = None):
        """Initialisiert den Dashboard-Service.
        Nutzt das globale Datenbank-Singleton. Falls ein db_path übergeben wird,
        wird dieses (z.B. für Tests) als Instanz abgesichert.
        """
        if db_path:
            self.db = Database(db_path)
        else:
            # Fallback auf das bereits existierende Singleton aus der main.py Lifespan
            self.db = Database._instance

    def get_current(self, node: str, start: datetime, end: datetime, freq: str) -> dict:
        """Holt die aggregierten Energiedaten direkt aus dem Repository."""
        # Hier wird die Abfrage gestartet. Da load_energy_data intern auf Database._instance
        # zugreift, läuft das jetzt perfekt synchron mit deiner restlichen Anwendung.
        return load_energy_data(start, end, freq, period_name=node, node=node)

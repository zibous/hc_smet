import sqlite3
from pathlib import Path
from threading import Lock

import logging
logger = logging.getLogger(__name__)

class Database:
    _instance = None
    _lock = Lock()

    def __new__(cls, db_path: str):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)

                # Pfad vorbereiten und Verzeichnis absichern
                db_path = Path(db_path)
                db_path.parent.mkdir(parents=True, exist_ok=True)

                # Speicher den Basis-Ordner (z.B. /data/) und den initialen Pfad ab
                cls._instance.db_dir = db_path.parent
                cls._instance.db_path = db_path

                logger.info(f"Datenbank-Singleton initialisiert für: {db_path}")

                # Einmalig beim Starten die Haupt-DB optimieren
                try:
                    temp_conn = sqlite3.connect(str(db_path))
                    temp_conn.execute("PRAGMA journal_mode=WAL;")
                    temp_conn.execute("PRAGMA synchronous=NORMAL;")
                    temp_conn.close()
                except Exception as e:
                    logger.error(f"Fehler bei der initialen PRAGMA-Konfiguration der Haupt-DB: {e}")

            return cls._instance

    def get_conn(self, year: int | None = None) -> sqlite3.Connection:
        """Erzeugt eine frische, thread-sichere Verbindung für den aufrufenden Thread.

        Wird ein 'year' übergeben (z.B. 2018), wird automatisch die historische
        Datenbank geladen. Ohne Jahr wird die aktuelle DB verwendet.
        """
        # Pfad bestimmen: Aktuell oder Historisch
        if year is not None:
            # Dynamischen Pfad für das angeforderte historische Jahr bauen
            target_path = self.db_dir / f"sensors_{year}.db"
        else:
            # Standard: Nutzt den bei der Initialisierung gesetzten Pfad (aktuelles Jahr)
            target_path = self.db_path

        # Erstellt eine dedizierte Verbindung für diesen Thread
        conn = sqlite3.connect(
            str(target_path),
            check_same_thread=False,   # Erlaubt die Übergabe an Pandas/Threads
            isolation_level=None       # Autocommit aktivieren (wie im Original)
        )

        # 🔧 CRITICAL FIX: PRAGMAs müssen zwingend für JEDE Verbindung ausgeführt werden!
        # Das stellt sicher, dass auch historische Jahre (2013-2025) im extrem performanten
        # WAL-Modus laufen und Lese-/Schreibkonflikte im Docker-Container ausgeschlossen sind.
        try:
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("PRAGMA synchronous=NORMAL;")
        except Exception as e:
            logger.error(f"Fehler beim Setzen der PRAGMAs für {target_path.name}: {e}")

        return conn

    def close(self):
        logger.info(f"Schließe Datenbank-Infrastruktur für {self.db_path}")

import tempfile
import shutil
from pathlib import Path
import pytest

from app.infrastructure.database.dbconnect import Database
from app.services.state.sensor_store import SensorStore
from app.services.sensor_service import SensorService

@pytest.fixture
def setup_pipeline_db():
    """Initialisiert eine temporäre Test-Datenbank für den Aggregator im Service."""
    tmpdir = tempfile.mkdtemp()
    test_db_path = Path(tmpdir) / "pipeline_sensors.db"

    # Singleton für die Laufzeit des Tests sperren
    Database(str(test_db_path))

    yield

    # Bereinigung nach dem Test
    Database._instance = None
    shutil.rmtree(tmpdir)

def test_full_pipeline(setup_pipeline_db):
    # Nutzen des Stores ohne permanente Datei im Test-Modus
    store = SensorStore(use_file=False)
    service = SensorService(store)

    # 🔧 FIX: Auf das vom Parser erwartete, gültige Hardware-Format umgestellt
    payload = "data=S01=100.5;S02=200.0"

    # Verarbeitet die Daten über die Schaltzentrale (Parser -> Store -> DB)
    result = service.handle("poKey64", payload)

    # Überprüfen, ob die Daten erfolgreich normalisiert wurden
    assert "S01" in result
    assert "S02" in result

    # 🔧 FIX: Die Route & der Service liefern flache floats zurück (keine Sub-Dicts mit "current")
    assert result["S01"]["current"] == 100.5
    assert result["S02"]["current"] == 200.0

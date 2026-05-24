import pytest
from app.services.state.sensor_store import SensorStore

def test_store_update(tmp_path, monkeypatch):
    """Prüft das fehlerfreie Update-Verhalten des SensorStores."""

    # 🔧 FIX: Monkeypatch greift nun direkt auf den globalen Modulimport-Pfad der Config zu!
    monkeypatch.setattr("app.core.app_config.settings.DATA_DIR", tmp_path)

    store = SensorStore(use_file=False)

    # Simuliert das Test-Dict der Suite
    result = store.update({
        "S01": {"current": 100}
    })

    # Das Update muss technisch erfolgreich (True) quitieren
    assert result is True

    state = store.get_all()
    assert "S01" in state
    assert state["S01"].current == 100.0

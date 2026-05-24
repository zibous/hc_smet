import pytest
from app.services.state.sensor_store import SensorStore

def test_store_update(tmp_path, monkeypatch):
    """Prüft das fehlerfreie Update-Verhalten des SensorStores."""

    # 🔧 FINALER FIX: Der Pfad greift nun direkt auf das globale app_config-Modul zu!
    monkeypatch.setattr("app.core.app_config.settings.DATA_DIR", tmp_path)

    store = SensorStore(use_file=False)

    # Füttert den Store mit dem verschachtelten Test-Dictionary
    result = store.update({
        "S01": {"current": 100}
    })

    # Das RAM-Update muss technisch mit True quittieren
    assert result is True

    state = store.get_all()
    assert "S01" in state
    assert state["S01"].current == 100.0

import time
import pytest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch
from app.services.state.sensor_store import SensorStore
from app.services.sensor_service import SensorService
from app.schemas.sensors import SensorStateEntry

def test_sensor_store_counter_overflow():
    store = SensorStore(use_file=False)
    store.update({"S01": 9999.0})
    state_1 = store.get_all()["S01"]
    assert state_1.current == 9999.0
    assert state_1.delta == 0.0

    store.update({"S01": 10.0})
    state_2 = store.get_all()["S01"]

    assert state_2.current == 10.0
    assert state_2.delta == 0.0
    assert state_2.last == 10.0

def test_mitternacht_jahreswechsel(tmp_path, monkeypatch):
    # 🔧 FIX: Monkeypatch zielt direkt auf den korrekten Modul-Import-Pfad
    monkeypatch.setattr("app.core.app_config.settings.DB_PATH", tmp_path)
    monkeypatch.setattr("app.core.app_config.settings.DATA_DIR", tmp_path)

    store = SensorStore(use_file=True)
    sensor_service = SensorService(store)

    # SCHRITT A: SILVESTER (31.12.2025)
    with patch("app.core.app_config.datetime") as mock_datetime:
        mock_datetime.now.return_value = datetime(2025, 12, 31, 23, 55, 0)

        payload_silvester = "data=S01=5000.0"
        sensor_service.handle("poKey64", payload_silvester)

        state_silvester = store.get_all()["S01"]
        assert state_silvester.current == 5000.0
        assert state_silvester.delta == 0.0

    # SCHRITT B: NEUJAHR (01.01.2026)
    with patch("app.core.app_config.datetime") as mock_datetime:
        mock_datetime.now.return_value = datetime(2026, 1, 1, 0, 5, 0)

        # 🔧 FIX: Variable korrekt benannt und Wert erhöht, damit Delta=2.5 stimmt!
        payload_neujahr = "data=S01=5002.5"
        sensor_service.handle("poKey64", payload_neujahr)

        state_neujahr = store.get_all()["S01"]
        assert state_neujahr.current == 5002.5
        assert state_neujahr.last == 5000.0
        assert state_neujahr.delta == 2.5

    assert (tmp_path / "sensor_state.json").exists()

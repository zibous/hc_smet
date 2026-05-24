"""Shared fixtures for v3 refactoring tests."""

import sqlite3
import tempfile
from pathlib import Path
import pytest


@pytest.fixture
def tmp_db(tmp_path):
    """Creates a temporary SQLite database with the hourly_values schema."""
    db_path = tmp_path / "test_sensors.db"
    conn = sqlite3.connect(str(db_path))
    conn.executescript("""
        CREATE TABLE hourly_values (
            sensor_id TEXT NOT NULL,
            hour INTEGER NOT NULL,
            consumption REAL NOT NULL,
            total REAL,
            PRIMARY KEY (sensor_id, hour)
        );
        CREATE INDEX IF NOT EXISTS idx_hour ON hourly_values(hour);
    """)
    conn.close()
    return db_path


@pytest.fixture
def mock_db_instance(tmp_db, monkeypatch):
    """Patches Database._instance to use the temp DB."""
    from app.infrastructure.database.dbconnect import Database

    # Create a minimal mock that provides get_conn()
    class MockDatabase:
        def __init__(self, path):
            self.db_path = Path(path)

        def get_conn(self, year=None):
            return sqlite3.connect(str(self.db_path), check_same_thread=False)

    instance = MockDatabase(tmp_db)
    monkeypatch.setattr(Database, "_instance", instance)
    return instance


@pytest.fixture
def sensor_store(tmp_path, mock_db_instance):
    """Creates a SensorStore with file persistence and DB enabled."""
    from app.services.state.sensor_store import SensorStore

    json_path = tmp_path / "sensor_state.json"
    store = SensorStore(file_path=str(json_path), use_file=True, db_enabled=True)
    return store


@pytest.fixture
def sensor_store_no_db(tmp_path):
    """Creates a SensorStore without DB (for pure RAM/JSON tests)."""
    from app.services.state.sensor_store import SensorStore

    json_path = tmp_path / "sensor_state.json"
    store = SensorStore(file_path=str(json_path), use_file=True, db_enabled=False)
    return store

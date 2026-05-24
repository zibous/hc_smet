"""Root conftest — shared fixtures for all tests."""

import tempfile
import shutil
from pathlib import Path
import pytest

from app.infrastructure.database.dbconnect import Database


@pytest.fixture
def tmp_database():
    """Erstellt eine temporäre SQLite-Datenbank für Tests."""
    tmpdir = tempfile.mkdtemp()
    test_db_path = Path(tmpdir) / "test_sensors.db"

    db_instance = Database(str(test_db_path))

    yield db_instance

    Database._instance = None
    shutil.rmtree(tmpdir)

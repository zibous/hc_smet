"""Tests für den refactored SensorStore (v3).

Testet:
- Kalibrierung (erster Wert → delta=0, nichts in DB)
- Normaler Folgewert (delta korrekt, in DB geschrieben)
- Zähler-Reset (delta=0, nichts in DB)
- Zeitlücke > 1h (gleichmäßige Verteilung)
- JSON-Persistenz (Laden/Speichern)
- DB-Recovery (Fallback wenn JSON fehlt)
"""

import sqlite3
import time
import json
from pathlib import Path


class TestKalibrierung:
    """Erster Wert für einen Sensor → delta=0, nichts in DB."""

    def test_erster_wert_delta_null(self, sensor_store):
        """Beim ersten Kontakt muss delta=0 sein."""
        sensor_store.update({"S01": 948.50})

        state = sensor_store.get_all()
        assert "S01" in state
        assert state["S01"].current == 948.50
        assert state["S01"].delta == 0.0

    def test_erster_wert_kein_db_eintrag(self, sensor_store, mock_db_instance):
        """Beim ersten Kontakt darf NICHTS in hourly_values stehen."""
        sensor_store.update({"S01": 948.50})

        conn = mock_db_instance.get_conn()
        count = conn.execute("SELECT COUNT(*) FROM hourly_values").fetchone()[0]
        conn.close()
        assert count == 0

    def test_mehrere_sensoren_kalibrierung(self, sensor_store):
        """Alle Sensoren im ersten Paket werden kalibriert."""
        sensor_store.update({"S01": 948.50, "S02": 2044.36, "S03": 53.16})

        state = sensor_store.get_all()
        assert len(state) == 3
        for entry in state.values():
            assert entry.delta == 0.0


class TestNormalerFolgewert:
    """Zweiter Wert → delta korrekt berechnet und in DB geschrieben."""

    def test_delta_berechnung(self, sensor_store):
        """delta = current - last, gerundet auf 6 Stellen."""
        sensor_store.update({"S01": 948.50})
        sensor_store.update({"S01": 948.53})

        state = sensor_store.get_all()
        assert state["S01"].delta == 0.03
        assert state["S01"].current == 948.53
        assert state["S01"].last == 948.50

    def test_delta_in_db_geschrieben(self, sensor_store, mock_db_instance):
        """Das Delta muss in hourly_values landen."""
        from app.core.app_config import settings
        
        sensor_store.update({"S01": 948.50})
        sensor_store.update({"S01": 948.53})

        conn = mock_db_instance.get_conn()
        row = conn.execute(
            "SELECT consumption, total FROM hourly_values WHERE sensor_id='S01'"
        ).fetchone()
        conn.close()

        assert row is not None
        # Delta wird mit SENSOR_SCALE_FACTOR skaliert: 0.03 × 0.1 = 0.003
        expected_consumption = 0.03 * settings.SENSOR_SCALE_FACTOR
        assert abs(row[0] - expected_consumption) < 0.0001
        assert row[1] == 948.53  # total = aktueller Zählerstand

    def test_delta_null_kein_db_eintrag(self, sensor_store, mock_db_instance):
        """Wenn current == last (delta=0), darf nichts geschrieben werden."""
        sensor_store.update({"S01": 948.50})
        sensor_store.update({"S01": 948.50})  # Gleicher Wert

        conn = mock_db_instance.get_conn()
        count = conn.execute("SELECT COUNT(*) FROM hourly_values").fetchone()[0]
        conn.close()
        assert count == 0

    def test_mehrere_updates_addieren(self, sensor_store, mock_db_instance):
        """Mehrere Deltas in der gleichen Stunde werden addiert."""
        from app.core.app_config import settings
        
        sensor_store.update({"S01": 100.0})
        sensor_store.update({"S01": 100.01})
        sensor_store.update({"S01": 100.03})

        conn = mock_db_instance.get_conn()
        row = conn.execute(
            "SELECT consumption FROM hourly_values WHERE sensor_id='S01'"
        ).fetchone()
        conn.close()

        # 0.01 + 0.02 = 0.03, skaliert mit SENSOR_SCALE_FACTOR
        expected_consumption = 0.03 * settings.SENSOR_SCALE_FACTOR
        assert row is not None
        assert abs(row[0] - expected_consumption) < 0.0001


class TestZaehlerReset:
    """current < last → delta=0, neuer Basiswert."""

    def test_reset_delta_null(self, sensor_store):
        """Bei Zähler-Reset muss delta=0 sein."""
        sensor_store.update({"S01": 948.50})
        sensor_store.update({"S01": 0.0})  # Reset!

        state = sensor_store.get_all()
        assert state["S01"].delta == 0.0
        assert state["S01"].current == 0.0

    def test_reset_kein_db_eintrag(self, sensor_store, mock_db_instance):
        """Bei Zähler-Reset darf nichts in die DB geschrieben werden."""
        sensor_store.update({"S01": 948.50})
        sensor_store.update({"S01": 0.0})

        conn = mock_db_instance.get_conn()
        count = conn.execute("SELECT COUNT(*) FROM hourly_values").fetchone()[0]
        conn.close()
        assert count == 0

    def test_nach_reset_normal_weiter(self, sensor_store, mock_db_instance):
        """Nach einem Reset muss der nächste Wert normal gebucht werden."""
        from app.core.app_config import settings
        
        sensor_store.update({"S01": 948.50})
        sensor_store.update({"S01": 0.0})   # Reset
        sensor_store.update({"S01": 0.05})  # Normaler Folgewert

        conn = mock_db_instance.get_conn()
        row = conn.execute(
            "SELECT consumption FROM hourly_values WHERE sensor_id='S01'"
        ).fetchone()
        conn.close()

        assert row is not None
        # Delta 0.05 skaliert mit SENSOR_SCALE_FACTOR
        expected_consumption = 0.05 * settings.SENSOR_SCALE_FACTOR
        assert abs(row[0] - expected_consumption) < 0.0001


class TestZeitluecke:
    """Zeitdiff > 1h → Delta wird verworfen (Kalibrierung)."""

    def test_zeitluecke_kein_db_eintrag(self, sensor_store, mock_db_instance):
        """Bei Zeitlücke > 1h darf NICHTS in die DB geschrieben werden."""
        from app.schemas.sensors import SensorStateEntry

        # Manuell einen alten State setzen (4 Stunden in der Vergangenheit)
        old_ts = int(time.time()) - 4 * 3600
        sensor_store.data["S01"] = SensorStateEntry(
            current=100.0, last=100.0, delta=0.0, timestamp=old_ts
        )
        sensor_store._calibrated_sensors.add("S01")

        # Neuer Wert kommt jetzt (4h später, 2.4 kWh mehr)
        sensor_store.update({"S01": 102.4})

        conn = mock_db_instance.get_conn()
        count = conn.execute("SELECT COUNT(*) FROM hourly_values").fetchone()[0]
        conn.close()

        # Nichts geschrieben — Delta wurde verworfen
        assert count == 0

    def test_nach_zeitluecke_normal_weiter(self, sensor_store, mock_db_instance):
        """Nach einer Zeitlücke muss der nächste Wert normal gebucht werden."""
        from app.core.app_config import settings
        from app.schemas.sensors import SensorStateEntry

        # Alten State setzen (4h in der Vergangenheit)
        old_ts = int(time.time()) - 4 * 3600
        sensor_store.data["S01"] = SensorStateEntry(
            current=100.0, last=100.0, delta=0.0, timestamp=old_ts
        )
        sensor_store._calibrated_sensors.add("S01")

        # Erster Wert nach Lücke — Delta verworfen
        sensor_store.update({"S01": 102.4})

        # Zweiter Wert (30s später) — normales Delta
        sensor_store.update({"S01": 102.43})

        conn = mock_db_instance.get_conn()
        row = conn.execute(
            "SELECT consumption FROM hourly_values WHERE sensor_id='S01'"
        ).fetchone()
        conn.close()

        assert row is not None
        # Delta 0.03 skaliert mit SENSOR_SCALE_FACTOR
        expected_consumption = 0.03 * settings.SENSOR_SCALE_FACTOR
        assert abs(row[0] - expected_consumption) < 0.001


class TestJsonPersistenz:
    """sensor_state.json wird korrekt geschrieben und geladen."""

    def test_save_and_load(self, tmp_path):
        """Nach update() muss die JSON-Datei den State enthalten."""
        from app.services.state.sensor_store import SensorStore

        json_path = tmp_path / "state.json"
        store = SensorStore(file_path=str(json_path), use_file=True, db_enabled=False)

        store.update({"S01": 948.50})
        store.update({"S01": 948.53})

        # Neuen Store laden (simuliert Neustart)
        store2 = SensorStore(file_path=str(json_path), use_file=True, db_enabled=False)

        state = store2.get_all()
        assert "S01" in state
        assert state["S01"].current == 948.53
        assert state["S01"].last == 948.50

    def test_neustart_kein_sprung(self, tmp_path):
        """Nach Neustart (JSON laden) darf kein Sprung entstehen."""
        from app.services.state.sensor_store import SensorStore

        json_path = tmp_path / "state.json"
        store = SensorStore(file_path=str(json_path), use_file=True, db_enabled=False)

        store.update({"S01": 948.50})
        store.update({"S01": 948.53})

        # Neustart
        store2 = SensorStore(file_path=str(json_path), use_file=True, db_enabled=False)
        store2.update({"S01": 948.56})

        state = store2.get_all()
        assert state["S01"].delta == 0.03  # Nicht 948.56 - 0 = riesiger Sprung!


class TestImportUebergang:
    """Sonderfall: DB hat Import-Daten, JSON fehlt → kein Sprung."""

    def test_import_dann_live(self, sensor_store, mock_db_instance):
        """Nach Import (JSON leer) darf der erste Wert nichts buchen."""
        # Simuliere: Import hat Daten in hourly_values, aber kein JSON
        conn = mock_db_instance.get_conn()
        conn.execute(
            "INSERT INTO hourly_values(sensor_id, hour, consumption) VALUES ('S32', 1779292800, 0.19)"
        )
        conn.commit()
        conn.close()

        # Erster Live-Wert (Kalibrierung)
        sensor_store.update({"S32": 23382.58})

        # Prüfe: Import-Stunde darf NICHT verändert worden sein
        conn = mock_db_instance.get_conn()
        row = conn.execute(
            "SELECT consumption FROM hourly_values WHERE sensor_id='S32' AND hour=1779292800"
        ).fetchone()
        conn.close()

        assert row[0] == 0.19  # Unverändert!

    def test_zweiter_wert_nach_import(self, sensor_store, mock_db_instance):
        """Der zweite Wert nach Import bucht ein normales kleines Delta."""
        from app.core.app_config import settings
        
        sensor_store.update({"S32": 23382.58})  # Kalibrierung
        sensor_store.update({"S32": 23382.61})  # Normaler Folgewert

        conn = mock_db_instance.get_conn()
        rows = conn.execute(
            "SELECT consumption FROM hourly_values WHERE sensor_id='S32'"
        ).fetchall()
        conn.close()

        # Nur ein Eintrag mit dem kleinen Delta (skaliert)
        assert len(rows) == 1
        expected_consumption = 0.03 * settings.SENSOR_SCALE_FACTOR
        assert abs(rows[0][0] - expected_consumption) < 0.0001


class TestJahreswechsel:
    """Automatischer Wechsel auf neue Jahres-DB."""

    def test_schreibt_in_richtige_jahres_db(self, tmp_path, monkeypatch):
        """Werte werden basierend auf dem hour-Timestamp in die richtige DB geschrieben."""
        import sqlite3
        from app.infrastructure.database.dbconnect import Database
        from app.services.state.sensor_store import SensorStore
        from app.schemas.sensors import SensorStateEntry

        # Mock Database._instance mit db_dir
        class MockDB:
            def __init__(self, db_dir):
                self.db_dir = db_dir
                self.db_path = db_dir / "sensors_2026.db"

            def get_conn(self, year=None):
                if year:
                    path = self.db_dir / f"sensors_{year}.db"
                else:
                    path = self.db_path
                return sqlite3.connect(str(path), check_same_thread=False)

        mock = MockDB(tmp_path)
        monkeypatch.setattr(Database, "_instance", mock)

        json_path = tmp_path / "state.json"
        store = SensorStore(file_path=str(json_path), use_file=True, db_enabled=True)

        # Sensor kalibrieren
        store.update({"S01": 1000.0})

        # Wert in 2026 schreiben (hour = 1. Dez 2026, 10:00 UTC)
        import time
        # Manuell State setzen mit Timestamp in 2026
        ts_2026 = 1796310000  # ca. 2. Dez 2026
        store.data["S01"] = SensorStateEntry(current=1000.0, last=1000.0, delta=0.0, timestamp=ts_2026)
        store._calibrated_sensors.add("S01")

        # Nächster Wert 30s später (noch 2026)
        store.data["S01"] = SensorStateEntry(current=1000.0, last=1000.0, delta=0.0, timestamp=ts_2026)
        # Simuliere update mit neuem Wert
        import unittest.mock
        with unittest.mock.patch("time.time", return_value=ts_2026 + 30):
            store.update({"S01": 1000.05})

        # Prüfe: sensors_2026.db hat den Eintrag
        conn_2026 = sqlite3.connect(str(tmp_path / "sensors_2026.db"))
        rows_2026 = conn_2026.execute("SELECT * FROM hourly_values").fetchall()
        conn_2026.close()
        assert len(rows_2026) > 0

        # Jetzt Wert in 2027 schreiben (hour = 1. Jan 2027, 00:30 UTC)
        ts_2027 = 1798761600 + 1800  # 1. Jan 2027 00:30 UTC
        store.data["S01"] = SensorStateEntry(current=1000.05, last=1000.05, delta=0.0, timestamp=ts_2027 - 30)
        with unittest.mock.patch("time.time", return_value=ts_2027):
            store.update({"S01": 1000.10})

        # Prüfe: sensors_2027.db wurde erstellt und hat den Eintrag
        db_2027 = tmp_path / "sensors_2027.db"
        assert db_2027.exists()

        conn_2027 = sqlite3.connect(str(db_2027))
        rows_2027 = conn_2027.execute("SELECT * FROM hourly_values").fetchall()
        conn_2027.close()
        assert len(rows_2027) > 0

    def test_sensor_state_json_ueberlebt_jahreswechsel(self, tmp_path, monkeypatch):
        """sensor_state.json bleibt beim Jahreswechsel erhalten — kein Kalibrierungsverlust."""
        import sqlite3
        from app.infrastructure.database.dbconnect import Database
        from app.services.state.sensor_store import SensorStore

        class MockDB:
            def __init__(self, db_dir):
                self.db_dir = db_dir
                self.db_path = db_dir / "sensors_2026.db"

            def get_conn(self, year=None):
                if year:
                    path = self.db_dir / f"sensors_{year}.db"
                else:
                    path = self.db_path
                return sqlite3.connect(str(path), check_same_thread=False)

        mock = MockDB(tmp_path)
        monkeypatch.setattr(Database, "_instance", mock)

        json_path = tmp_path / "state.json"
        store = SensorStore(file_path=str(json_path), use_file=True, db_enabled=True)

        # Kalibrierung + normaler Wert
        store.update({"S32": 23415.0})
        store.update({"S32": 23415.05})

        # JSON existiert
        assert json_path.exists()

        # Neuen Store laden (simuliert App-Neustart am 1.1.)
        store2 = SensorStore(file_path=str(json_path), use_file=True, db_enabled=True)
        state = store2.get_all()

        # Kein Kalibrierungsverlust
        assert "S32" in state
        assert state["S32"].current == 23415.05
        assert "S32" in store2._calibrated_sensors

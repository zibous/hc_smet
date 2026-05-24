"""Tests für den vereinfachten SensorService (v3).

Testet:
- Parsing und Validierung der POST-Daten
- Korrekte Weiterleitung an SensorStore
- skip_db Flag
"""

import time


class TestSensorServiceBasic:
    """Grundlegende Verarbeitung von PoKeys-Daten."""

    def test_handle_pokey64_payload(self, sensor_store_no_db):
        """Verarbeitet ein typisches PoKey64-Telegramm."""
        from app.services.sensor_service import SensorService

        service = SensorService(sensor_store_no_db)
        payload = "data=S01=948.50;S02=2044.36;S03=53.16"

        result = service.handle(device="PoKey64", payload=payload)

        assert "S01" in result
        assert "S02" in result
        assert "S03" in result
        assert result["S01"]["current"] == 948.50

    def test_handle_pokey65_payload(self, sensor_store_no_db):
        """Verarbeitet ein typisches PoKey65-Telegramm."""
        from app.services.sensor_service import SensorService

        service = SensorService(sensor_store_no_db)
        payload = "data=S26=2811.73;S32=23408.86;S33=2632.22"

        result = service.handle(device="PoKey65", payload=payload)

        assert "S26" in result
        assert "S32" in result
        assert "S33" in result

    def test_handle_empty_payload(self, sensor_store_no_db):
        """Leerer Payload gibt leeres Dict zurück."""
        from app.services.sensor_service import SensorService

        service = SensorService(sensor_store_no_db)
        result = service.handle(device="PoKey64", payload="")

        assert result == {}

    def test_handle_invalid_values_skipped(self, sensor_store_no_db):
        """Ungültige Werte (negativ, zu hoch) werden übersprungen."""
        from app.services.sensor_service import SensorService

        service = SensorService(sensor_store_no_db)
        payload = "data=S01=948.50;S02=-5.0;S03=9999999"

        result = service.handle(device="PoKey64", payload=payload)

        assert "S01" in result
        assert "S02" not in result  # Negativ → abgelehnt
        assert "S03" not in result  # > 1M → abgelehnt


class TestSkipDb:
    """skip_db Flag verhindert DB-Schreibvorgänge."""

    def test_skip_db_no_write(self, sensor_store, mock_db_instance):
        """Mit skip_db=True darf nichts in die DB geschrieben werden."""
        from app.services.sensor_service import SensorService
        import sqlite3

        service = SensorService(sensor_store)

        # Kalibrierung
        service.handle(device="PoKey64", payload="data=S01=948.50", skip_db=False)
        # Zweiter Wert mit skip_db
        service.handle(device="PoKey64", payload="data=S01=948.53", skip_db=True)

        conn = mock_db_instance.get_conn()
        count = conn.execute("SELECT COUNT(*) FROM hourly_values").fetchone()[0]
        conn.close()

        assert count == 0  # Nichts geschrieben wegen skip_db

import time
import pytest
from app.infrastructure.database.dbconnect import Database

def test_first_insert(aggregator):
    aggregator.process("S01", 100, 1700000000)

    # 🔧 FIX: Frische Verbindung aus dem Singleton holen
    conn = Database._instance.get_conn()
    try:
        cur = conn.execute(
            "SELECT * FROM sensor_state WHERE sensor_id='S01'"
        ).fetchone()
        assert cur is not None
    finally:
        conn.close()


def test_delta_calculation(aggregator):
    t = 1700000000

    aggregator.process("S01", 100, t)
    aggregator.process("S01", 120, t + 3600)

    # 🔧 FIX: Frische Verbindung aus dem Singleton holen
    conn = Database._instance.get_conn()
    try:
        state = conn.execute(
            "SELECT last_value FROM sensor_state WHERE sensor_id='S01'"
        ).fetchone()
        assert state[0] == 120
    finally:
        conn.close()


def test_hourly_insert(aggregator):
    t = 1700000000

    aggregator.process("S01", 100, t)
    aggregator.process("S01", 150, t + 3600)

    # 🔧 FIX: Frische Verbindung aus dem Singleton holen
    conn = Database._instance.get_conn()
    try:
        row = conn.execute(
            "SELECT consumption FROM hourly_values WHERE sensor_id='S01'"
        ).fetchone()
        assert row is not None
        assert row[0] >= 0
    finally:
        conn.close()


def test_cleanup(aggregator):
    # Nutzen von aktuellen Timestamps, da die Cleanup-Logik relativ zur aktuellen Systemzeit filtert
    now_hour = (int(time.time()) // 3600) * 3600
    old_ts = now_hour - (40 * 86400) # Vor 40 Tagen (wird gelöscht)
    new_ts = now_hour - (5 * 86400)  # Vor 5 Tagen (bleibt erhalten)

    # Daten simulieren
    aggregator.process("S01", 100, old_ts)
    aggregator.process("S01", 150, old_ts + 3600)
    aggregator.process("S01", 200, new_ts)
    aggregator.process("S01", 250, new_ts + 3600)

    # Cleanup triggern (Standard: löscht alles älter als 30 Tage)
    aggregator.cleanup(retention_days=30)

    # 🔧 FIX: Frische Verbindung aus dem Singleton holen
    conn = Database._instance.get_conn()
    try:
        rows = conn.execute(
            "SELECT COUNT(*) FROM hourly_values"
        ).fetchone()[0]
        # Es sollte mindestens ein Eintrag (der von new_ts) übrig geblieben sein
        assert rows >= 1
    finally:
        conn.close()

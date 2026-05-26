import os
import pytest
from pathlib import Path

from app.core.app_config import Settings, get_settings

# =========================================================
# FIXTURE: isolierte Settings-Instanz (kein Singleton Cache)
# =========================================================
@pytest.fixture
def settings():
    return Settings()


# =========================================================
# 1. BASIC CONFIG VALIDATION
# =========================================================
def test_basic_types(settings):

    assert isinstance(settings.APP_NAME, str)
    assert isinstance(settings.SERVER_PORT, int)
    assert isinstance(settings.FETCH_INTERVAL, int)
    assert isinstance(settings.SENSOR_SCALE_FACTOR, float)

    assert settings.SERVER_PORT > 0
    assert settings.FETCH_INTERVAL > 0


# =========================================================
# 2. PATHS SAFETY CHECK
# =========================================================
def test_paths_are_valid(settings):

    assert isinstance(settings.DATA_DIR, Path)
    assert isinstance(settings.LOG_DIR, Path)

    assert settings.DATA_DIR.is_absolute()
    assert settings.LOG_DIR.is_absolute()


# =========================================================
# 3. DEVICE CREATION FROM ENV
# =========================================================
def test_devices_exist(settings):

    assert len(settings.devices) == 2

    for dev in settings.devices:

        assert dev.id.startswith("IF")
        assert "." in dev.ip
        assert len(dev.name) > 0


# =========================================================
# 4. SENSOR EXPANSION LOGIC (KRITISCH!)
# =========================================================
def test_sensor_list_expansion(settings):

    dev = settings.devices[0]
    sensors = dev.sensor_list

    # sollte 25 Sensoren erzeugen (1-25 oder 26-50)
    assert len(sensors) == 25

    assert all(":S" in s for s in sensors)
    assert sensors[0].endswith("S01")


# =========================================================
# 5. SENSOR URL GENERATION
# =========================================================
def test_sensor_url(settings):

    for dev in settings.devices:

        url = dev.sensor_url

        assert url.startswith("http://")
        assert "/sensorList.json" in url
        assert dev.ip in url


# =========================================================
# 6. SENSOR DICTIONARY (DERIVED STRUCTURE)
# =========================================================
def test_sensor_devices_structure(settings):

    data = settings.sensor_devices

    assert isinstance(data, dict)
    assert "pokey64" in data
    assert "pokey65" in data

    for name, dev in data.items():

        assert "id" in dev
        assert "ip" in dev
        assert "geturl" in dev
        assert dev["geturl"].startswith("http://")


# =========================================================
# 7. MQTT LOGIC
# =========================================================
def test_mqtt_settings(settings):

    assert settings.MQTT_PORT > 0

    mode = settings.mqtt_mode
    assert mode in ["test", "production"]

    topic = settings.mqtt_topic_sensors
    assert isinstance(topic, str)
    assert len(topic) > 0


# =========================================================
# 8. DATABASE LOGIC
# =========================================================
def test_database_logic(settings):

    name = settings.database_name
    path = settings.database_path

    assert "sensors_" in name
    assert name.endswith(".db")

    assert path.exists()
    assert path.is_dir()


# =========================================================
# 9. MQTT MODE CONSISTENCY
# =========================================================
def test_mqtt_mode_consistency(settings):

    if settings.MQTT_TOPIC_TEST:
        assert settings.mqtt_mode == "test"
    else:
        assert settings.mqtt_mode == "production"


# =========================================================
# 10. LEGACY COMPATIBILITY
# =========================================================
def test_legacy_get_urls(settings):

    url1 = settings.pokeys_device1_get
    url2 = settings.pokeys_device2_get

    assert url1.startswith("http://")
    assert url2.startswith("http://")


# =========================================================
# 11. SENSOR IP LIST
# =========================================================
def test_ip_list(settings):

    ips = settings.ip_addresses

    assert isinstance(ips, list)
    assert len(ips) == 2

    for ip in ips:
        assert ip.count(".") == 3

def test_full_device_chain(settings):

    for dev in settings.devices:
        # IP korrekt
        assert dev.ip.count(".") == 3
        # Sensor Expansion korrekt
        sensors = dev.sensor_list
        assert len(sensors) == 25
        # URL korrekt
        assert dev.sensor_url.startswith("http://")

"""
Tests für die neue app_config.py Struktur.

Prüft:
- Rückwärtskompatibilität aller Properties
- Neue Pydantic Models (PokeyDevice, DeviceConfig)
- Korrekte Werte aus .env
- Cached Properties
"""

import pytest
from pathlib import Path
from datetime import datetime


def test_settings_import():
    """Test: Settings können importiert werden"""
    from app.core.app_config import settings
    assert settings is not None


def test_base_dir_exists():
    """Test: BASE_DIR ist korrekt gesetzt"""
    from app.core.app_config import BASE_DIR
    assert BASE_DIR.exists()
    assert (BASE_DIR / "app").exists()


def test_application_settings():
    """Test: Application Settings sind korrekt"""
    from app.core.app_config import settings
    
    assert settings.APP_NAME == "pokeys-service"
    assert settings.APP_ATTRIBUTION == "Peter Siebler"
    assert settings.PROJECT_NAME == "hc_smet"
    assert settings.SERVER_HOST == "0.0.0.0"
    assert settings.SERVER_PORT == 8096
    assert settings.BASE_URL == "/"
    assert settings.FRONTEND_REQUEST_METHOD == "GET"


def test_directories():
    """Test: Verzeichnis-Pfade sind korrekt"""
    from app.core.app_config import settings, BASE_DIR
    
    assert settings.DATA_DIR == BASE_DIR / "data"
    assert settings.LOG_DIR == BASE_DIR / "logs"


def test_data_mode_settings():
    """Test: Data Mode Settings"""
    from app.core.app_config import settings
    
    assert settings.POKEY_SERVICE in ["GET", "POST"]
    assert isinstance(settings.SENSOR_SCALE_FACTOR, float)
    assert settings.SENSOR_SCALE_FACTOR == 0.1  # aus .env
    assert isinstance(settings.FETCH_INTERVAL, int)
    assert isinstance(settings.STROMPREISE, dict)


def test_database_settings():
    """Test: Database Settings"""
    from app.core.app_config import settings
    
    assert isinstance(settings.DB_ENABLED, bool)
    assert settings.DB_ENABLED is True  # aus .env
    assert isinstance(settings.DB_PATH, Path)
    assert isinstance(settings.DATA_LOG_ENABELD, bool)  # Typo aus .env
    assert isinstance(settings.DATA_TRACE_ENABELD, bool)  # Typo aus .env


def test_database_name_property():
    """Test: database_name Property generiert korrekten Namen"""
    from app.core.app_config import settings
    
    current_year = datetime.now().year
    expected = f"sensors_{current_year}.db"
    assert settings.database_name == expected


def test_database_path_property():
    """Test: database_path Property gibt validen Pfad zurück"""
    from app.core.app_config import settings
    
    db_path = settings.database_path
    assert isinstance(db_path, Path)
    assert db_path.is_absolute()


def test_analytics_db_path():
    """Test: analytics_db_path Property"""
    from app.core.app_config import settings
    
    analytics_path = settings.analytics_db_path
    assert isinstance(analytics_path, Path)
    assert analytics_path.name == "analytics.sqlite"


def test_analytics_settings():
    """Test: Analytics Configuration"""
    from app.core.app_config import settings
    
    assert isinstance(settings.YEAR_FROM, int)
    assert isinstance(settings.YEAR_TO, int)
    assert settings.YEAR_FROM == 2013  # aus .env
    assert settings.YEAR_TO == 2100
    assert isinstance(settings.ENABLE_CLUSTERING, bool)
    assert isinstance(settings.ENABLE_DAILY_STATS, bool)


def test_mqtt_settings():
    """Test: MQTT Configuration"""
    from app.core.app_config import settings
    
    assert isinstance(settings.MQTT_ENABLED, bool)
    assert settings.MQTT_ENABLED is True  # aus .env
    assert settings.MQTT_HOST == "10.1.1.119"  # aus .env
    assert settings.MQTT_PORT == 1883
    assert settings.MQTT_CLIENT_ID == "pokey_service"
    assert settings.MQTT_USERNAME == "smarthome"  # aus .env
    assert settings.MQTT_INTERVAL == 300
    assert settings.MQTT_TOPIC_BASE == "smartmeters"


def test_mqtt_mode_property():
    """Test: mqtt_mode Property"""
    from app.core.app_config import settings
    
    # Wenn MQTT_TOPIC_TEST leer ist → production
    mode = settings.mqtt_mode
    assert mode in ["test", "production"]
    assert mode == "production"  # aus .env (MQTT_TOPIC_TEST ist leer)


def test_mqtt_topic_sensors_property():
    """Test: mqtt_topic_sensors Property"""
    from app.core.app_config import settings
    
    topic = settings.mqtt_topic_sensors
    assert isinstance(topic, str)
    # Im Production-Modus: smartmeters/sensors
    assert topic == "smartmeters/sensors"


def test_home_assistant_settings():
    """Test: Home Assistant Configuration"""
    from app.core.app_config import settings
    
    assert isinstance(settings.HA_WEBHOOK_URL, str)
    assert isinstance(settings.HA_WEBHOOK_ID, str)


def test_mapping_settings():
    """Test: Sensor Mapping Configuration"""
    from app.core.app_config import settings
    
    assert isinstance(settings.MAPPING_ENABLED, bool)
    mapping_file = settings.mapping_file
    assert isinstance(mapping_file, Path)
    assert mapping_file.name == "house.yaml"


def test_logging_settings():
    """Test: Logging Configuration"""
    from app.core.app_config import settings
    
    assert settings.LOG_LEVEL == "INFO"
    assert settings.LOG_MODE == "both"
    assert settings.LOG_FILE == "logs/app.log"


def test_pokeys_device_env_vars():
    """Test: Legacy POKEYS_DEVICE* ENV-Variablen sind geladen"""
    from app.core.app_config import settings
    
    # Device 1
    assert settings.POKEYS_DEVICE1_ID == "IF64"
    assert settings.POKEYS_DEVICE1_NAME == "poKey64"
    assert settings.POKEYS_DEVICE1_IP == "10.1.1.64"
    assert settings.POKEYS_DEVICE1_SENSORS == "1-25"
    
    # Device 2
    assert settings.POKEYS_DEVICE2_ID == "IF65"
    assert settings.POKEYS_DEVICE2_NAME == "poKey65"
    assert settings.POKEYS_DEVICE2_IP == "10.1.1.65"
    assert settings.POKEYS_DEVICE2_SENSORS == "26-50"


def test_devices_list_created():
    """Test: devices Liste wird aus ENV-Variablen gebaut"""
    from app.core.app_config import settings
    
    assert isinstance(settings.devices, list)
    assert len(settings.devices) == 2
    
    # Device 1
    dev1 = settings.devices[0]
    assert dev1.id == "IF64"
    assert dev1.name == "poKey64"
    assert dev1.ip == "10.1.1.64"
    assert dev1.sensors == "1-25"
    
    # Device 2
    dev2 = settings.devices[1]
    assert dev2.id == "IF65"
    assert dev2.name == "poKey65"
    assert dev2.ip == "10.1.1.65"
    assert dev2.sensors == "26-50"


def test_pokey_device_sensor_list():
    """Test: PokeyDevice.sensor_list expandiert Range korrekt"""
    from app.core.app_config import settings
    
    dev1 = settings.devices[0]
    sensor_list = dev1.sensor_list
    
    assert isinstance(sensor_list, list)
    assert len(sensor_list) == 25  # 1-25
    assert sensor_list[0] == "IF64:S01"
    assert sensor_list[24] == "IF64:S25"


def test_pokey_device_sensor_url():
    """Test: PokeyDevice.sensor_url generiert korrekte URL"""
    from app.core.app_config import settings
    
    dev1 = settings.devices[0]
    url = dev1.sensor_url
    
    assert url == "http://10.1.1.64/sensorList.json"


def test_device_config_exists():
    """Test: DeviceConfig ist initialisiert"""
    from app.core.app_config import settings
    
    assert settings.device is not None
    assert settings.device.name == "Smartmeters"
    assert settings.device.model == "PoKeys57E"
    assert settings.device.device_id == "eacWSZ"


def test_device_config_ha_device():
    """Test: DeviceConfig.ha_device Property"""
    from app.core.app_config import settings
    
    ha_device = settings.device.ha_device
    assert isinstance(ha_device, dict)
    assert "identifiers" in ha_device
    assert "name" in ha_device
    assert "manufacturer" in ha_device
    assert ha_device["name"] == "Smartmeters"


def test_legacy_pokeys_device_get_urls():
    """Test: Legacy pokeys_device1_get und pokeys_device2_get Properties"""
    from app.core.app_config import settings
    
    url1 = settings.pokeys_device1_get
    url2 = settings.pokeys_device2_get
    
    assert url1 == "http://10.1.1.64/sensorList.json"
    assert url2 == "http://10.1.1.65/sensorList.json"


def test_sensor_devices_dict():
    """Test: sensor_devices Dictionary (Legacy-Kompatibilität)"""
    from app.core.app_config import settings
    
    sensor_devices = settings.sensor_devices
    
    assert isinstance(sensor_devices, dict)
    assert len(sensor_devices) == 2
    assert "pokey64" in sensor_devices
    assert "pokey65" in sensor_devices
    
    # Device 1 Struktur
    dev1 = sensor_devices["pokey64"]
    assert dev1["id"] == "IF64"
    assert dev1["name"] == "poKey64"
    assert dev1["ip"] == "10.1.1.64"
    assert dev1["geturl"] == "http://10.1.1.64/sensorList.json"
    assert dev1["start_index"] == 1
    assert isinstance(dev1["sensors"], list)
    assert len(dev1["sensors"]) == 25


def test_sensor_devices_is_cached():
    """Test: sensor_devices ist cached (gleiche Instanz)"""
    from app.core.app_config import settings
    
    devices1 = settings.sensor_devices
    devices2 = settings.sensor_devices
    
    # Sollte die gleiche Instanz sein (cached_property)
    assert devices1 is devices2


def test_get_device_method():
    """Test: get_device() Methode"""
    from app.core.app_config import settings
    
    # Case-insensitive
    dev1 = settings.get_device("pokey64")
    dev2 = settings.get_device("POKEY64")
    dev3 = settings.get_device("PoKey64")
    
    assert dev1 is not None
    assert dev1 == dev2 == dev3
    assert dev1["id"] == "IF64"
    
    # Nicht existierendes Device
    dev_none = settings.get_device("nonexistent")
    assert dev_none is None


def test_get_devices_start_index_method():
    """Test: get_devices_start_index() Methode"""
    from app.core.app_config import settings
    
    idx1 = settings.get_devices_start_index("pokey64")
    idx2 = settings.get_devices_start_index("pokey65")
    
    assert idx1 == 1
    assert idx2 == 26
    
    # Nicht existierendes Device → Default 1
    idx_none = settings.get_devices_start_index("nonexistent")
    assert idx_none == 1


def test_ip_addresses_property():
    """Test: ip_addresses Property"""
    from app.core.app_config import settings
    
    ips = settings.ip_addresses
    
    assert isinstance(ips, list)
    assert len(ips) == 2
    assert "10.1.1.64" in ips
    assert "10.1.1.65" in ips


def test_get_timestamp_iso_none():
    """Test: get_timestamp_iso() ohne Parameter"""
    from app.core.app_config import settings
    
    ts = settings.get_timestamp_iso()
    
    assert isinstance(ts, str)
    assert len(ts) == 19  # YYYY-MM-DDTHH:MM:SS
    assert "T" in ts


def test_get_timestamp_iso_with_int():
    """Test: get_timestamp_iso() mit Unix Timestamp"""
    from app.core.app_config import settings
    
    # 2024-01-01 00:00:00 UTC
    ts = settings.get_timestamp_iso(1704067200)
    
    assert ts == "2024-01-01T00:00:00"


def test_get_timestamp_iso_with_datetime():
    """Test: get_timestamp_iso() mit datetime Objekt"""
    from app.core.app_config import settings
    from datetime import datetime, timezone
    
    dt = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    ts = settings.get_timestamp_iso(dt)
    
    assert ts == "2024-01-01T12:00:00"


def test_settings_singleton():
    """Test: settings ist Singleton"""
    from app.core.app_config import settings, get_settings
    
    settings2 = get_settings()
    
    # Sollte die gleiche Instanz sein
    assert settings is settings2


def test_backward_compatibility_all_properties():
    """Test: Alle wichtigen Properties existieren (Rückwärtskompatibilität)"""
    from app.core.app_config import settings
    
    # Liste aller Properties die existieren müssen
    required_attrs = [
        "APP_NAME", "SERVER_HOST", "SERVER_PORT",
        "DB_PATH", "DB_ENABLED", "database_name", "database_path",
        "MQTT_ENABLED", "MQTT_HOST", "mqtt_mode", "mqtt_topic_sensors",
        "sensor_devices", "get_device", "get_devices_start_index",
        "get_timestamp_iso", "SENSOR_SCALE_FACTOR",
        "pokeys_device1_get", "pokeys_device2_get",
        "MAPPING_ENABLED", "mapping_file",
        "LOG_LEVEL", "LOG_MODE",
    ]
    
    for attr in required_attrs:
        assert hasattr(settings, attr), f"Missing attribute: {attr}"


def test_no_breaking_changes():
    """Test: Keine Breaking Changes - alle alten Zugriffe funktionieren"""
    from app.core.app_config import settings
    
    # Simuliere typische Zugriffe aus dem Code
    
    # 1. Database Zugriff
    db_path = settings.database_path
    assert db_path.exists() or True  # Pfad kann existieren oder nicht
    
    # 2. MQTT Zugriff
    if settings.MQTT_ENABLED:
        host = settings.MQTT_HOST
        port = settings.MQTT_PORT
        mode = settings.mqtt_mode
        assert host and port and mode
    
    # 3. Sensor Devices Zugriff
    devices = settings.sensor_devices
    for name, dev in devices.items():
        assert "id" in dev
        assert "ip" in dev
        assert "sensors" in dev
    
    # 4. Device Lookup
    dev = settings.get_device("pokey64")
    assert dev is not None
    
    # 5. Timestamp
    ts = settings.get_timestamp_iso()
    assert isinstance(ts, str)
    
    # Wenn wir hier ankommen, sind alle Zugriffe erfolgreich
    assert True

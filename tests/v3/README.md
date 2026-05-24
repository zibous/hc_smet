# Tests v3 - App Config Refactoring

## Übersicht

Diese Tests prüfen die neue `app_config.py` Struktur auf:
- ✅ Rückwärtskompatibilität
- ✅ Korrekte Werte aus `.env`
- ✅ Neue Pydantic Models
- ✅ Cached Properties
- ✅ Alle Legacy-Properties

## Tests ausführen

### Im Docker Container (empfohlen):

```bash
# Alle app_config Tests
make test-config

# Mit Details
make test-config-verbose

# Alle v3 Tests
make test-v3
```

### Direkt mit pytest:

```bash
# Einzelner Test
pytest -v tests/v3/test_app_config.py

# Mit Output
pytest -vv tests/v3/test_app_config.py -s

# Nur bestimmte Tests
pytest -v tests/v3/test_app_config.py -k "test_mqtt"
```

## Test-Struktur

### `test_app_config.py` (40+ Tests)

**Import & Basis:**
- `test_settings_import()` - Settings können importiert werden
- `test_base_dir_exists()` - BASE_DIR ist korrekt
- `test_settings_singleton()` - Singleton-Pattern funktioniert

**Application Settings:**
- `test_application_settings()` - APP_NAME, SERVER_HOST, etc.
- `test_directories()` - DATA_DIR, LOG_DIR

**Database:**
- `test_database_settings()` - DB_ENABLED, DB_PATH
- `test_database_name_property()` - Dynamischer DB-Name
- `test_database_path_property()` - Validierter Pfad
- `test_analytics_db_path()` - Analytics DB

**MQTT:**
- `test_mqtt_settings()` - MQTT_HOST, MQTT_PORT, etc.
- `test_mqtt_mode_property()` - test/production Mode
- `test_mqtt_topic_sensors_property()` - Topic-Generierung

**Devices (Neue Struktur):**
- `test_devices_list_created()` - Liste aus ENV gebaut
- `test_pokey_device_sensor_list()` - Range-Expansion
- `test_pokey_device_sensor_url()` - URL-Generierung
- `test_device_config_exists()` - DeviceConfig Model
- `test_device_config_ha_device()` - HA Discovery

**Legacy-Kompatibilität:**
- `test_legacy_pokeys_device_get_urls()` - Alte Properties
- `test_sensor_devices_dict()` - Legacy Dictionary
- `test_sensor_devices_is_cached()` - Caching funktioniert
- `test_get_device_method()` - get_device() Methode
- `test_get_devices_start_index_method()` - Start-Index
- `test_ip_addresses_property()` - IP-Liste

**Timestamp Helpers:**
- `test_get_timestamp_iso_none()` - Ohne Parameter
- `test_get_timestamp_iso_with_int()` - Unix Timestamp
- `test_get_timestamp_iso_with_datetime()` - datetime Objekt

**Rückwärtskompatibilität:**
- `test_backward_compatibility_all_properties()` - Alle Properties existieren
- `test_no_breaking_changes()` - Keine Breaking Changes

## Erwartete Ergebnisse

Alle Tests sollten **PASSED** sein:

```
tests/v3/test_app_config.py::test_settings_import PASSED
tests/v3/test_app_config.py::test_base_dir_exists PASSED
tests/v3/test_app_config.py::test_application_settings PASSED
...
tests/v3/test_app_config.py::test_no_breaking_changes PASSED

======================== 40+ passed in 0.5s ========================
```

## Bei Fehlern

### Import-Fehler:
```
ModuleNotFoundError: No module named 'pydantic'
```
→ Dependencies installieren: `pip install -r requirements.txt`

### Werte stimmen nicht:
```
AssertionError: assert 'localhost' == '10.1.1.119'
```
→ `.env` Datei prüfen, Service neu starten

### Property fehlt:
```
AttributeError: 'Settings' object has no attribute 'xyz'
```
→ Breaking Change! Property muss in app_config.py hinzugefügt werden

## Neue Features testen

Nach Änderungen an `app_config.py`:

1. **Test hinzufügen** in `test_app_config.py`
2. **Test ausführen**: `make test-config`
3. **Rückwärtskompatibilität prüfen**: `test_no_breaking_changes` muss PASSED sein

## Weitere Tests

- `test_sensor_service.py` - SensorService Tests
- `test_sensor_store.py` - SensorStore Tests

Siehe `conftest.py` für Fixtures.

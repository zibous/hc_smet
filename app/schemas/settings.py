from pydantic import BaseModel, ConfigDict
from pathlib import Path

class SettingsSchema(BaseModel):
    """Definiert die reine Datenstruktur und Typsicherheit deiner zentralen Konfiguration."""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    # APPLICATION
    APP_NAME: str
    PROJECT_NAME: str
    SERVER_HOST: str
    SERVER_PORT: int
    BASE_URL: str
    DATA_DIR: Path
    LOG_DIR: Path

    # DATA MODE
    POKEY_SERVICE: str
    FETCH_INTERVAL: int

    # DATABASE
    DB_PATH: Path
    DB_ENABLED: bool

    # ANALYTICS
    YEAR_FROM: int
    YEAR_TO: int
    ENABLE_CLUSTERING: bool
    ENABLE_DAILY_STATS: bool

    # MQTT
    MQTT_ENABLED: bool
    MQTT_HOST: str
    MQTT_PORT: int
    MQTT_CLIENT_ID: str
    MQTT_USERNAME: str
    MQTT_PASSWORD: str
    MQTT_TOPIC_TEST: str
    MQTT_TOPIC_BASE: str

    # SENSOR MAPPING
    MAPPING_ENABLED: bool
    _MAPPING_FILE: str

    # LOGGING
    LOG_LEVEL: str
    LOG_MODE: str
    LOG_FILE: str

    # POKEYS DEVICES
    POKEYS_DEVICE1_ID: str
    POKEYS_DEVICE1_NAME: str
    POKEYS_DEVICE1_IP: str
    POKEYS_DEVICE1_SENSORS: str
    POKEYS_DEVICE2_ID: str
    POKEYS_DEVICE2_NAME: str
    POKEYS_DEVICE2_IP: str
    POKEYS_DEVICE2_SENSORS: str
    SENSOR_PER_DEVICE: int

    # API CONFIGURATION
    FRONTEND_REQUEST_METHOD: str  # "GET" oder "POST"

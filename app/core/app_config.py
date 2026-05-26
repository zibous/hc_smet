from __future__ import annotations

import os
import json
from datetime import datetime, timezone
from functools import cached_property, lru_cache
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from pydantic import BaseModel, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# =================================================================
# 🔧 PORTABLE ROOT DISCOVERY
# =================================================================
CURRENT_FILE = Path(__file__).resolve()

if "app" in CURRENT_FILE.parts:
    BASE_DIR = CURRENT_FILE.parents[2]
else:
    BASE_DIR = (
        CURRENT_FILE.parents[0]
        if (CURRENT_FILE.parent / "app").exists()
        else CURRENT_FILE.parents[1]
    )

if not (BASE_DIR / "app").exists():
    for parent in CURRENT_FILE.parents:
        if (parent / "app" / "main.py").exists() or (parent / "main.py").exists():
            BASE_DIR = parent
            break

load_dotenv(BASE_DIR / ".env")


# =================================================================
# DEVICE MODELS
# =================================================================
class InterfaceConfig(BaseModel):
    """Interface configuration for PoKeys devices"""
    pokey64: bool = False
    pokey65: bool = False
    data: dict[str, Any] = Field(default_factory=dict)


class PokeyDevice(BaseModel):
    """Single PoKeys device configuration"""
    id: str
    name: str
    ip: str
    sensors: str

    @property
    def sensor_list(self) -> list[str]:
        """Expandiert Sensor-Range zu Liste: '1-25' → ['IF64:S01', ..., 'IF64:S25']"""
        result = []
        for part in self.sensors.split(","):
            part = part.strip()
            if "-" in part:
                start, end = map(int, part.split("-"))
                result.extend(
                    [f"{self.id}:S{str(i).zfill(2)}" for i in range(start, end + 1)]
                )
            else:
                i = int(part)
                result.append(f"{self.id}:S{str(i).zfill(2)}")
        return result

    @property
    def sensor_url(self) -> str:
        """GET URL für sensorList.json"""
        return f"http://{self.ip}/sensorList.json"


class DeviceConfig(BaseModel):
    """Home Assistant Discovery Configuration"""
    name: str = "Smartmeters"
    location: str = ""
    manufacturer: str = "PoLabs d.o.o, Volavlje 30,1000 Ljubljana,Slovenija"
    model: str = "PoKeys57E"
    device_id: str = "eacWSZ"
    latitude: float = 47.4594353
    longitude: float = 9.6361833
    protocol: str = "PoLabs Json"
    firmware: str = "2017 PoLabs"
    description: str = "Ethernet I/O controller PoKeys57E"
    interfaces: InterfaceConfig = Field(default_factory=InterfaceConfig)

    @property
    def ha_device(self) -> dict[str, Any]:
        """Home Assistant Device Dictionary"""
        return {
            "identifiers": [self.device_id],
            "name": self.name,
            "manufacturer": self.manufacturer,
            "model": self.model,
            "sw_version": self.firmware,
        }


# =================================================================
# MAIN SETTINGS
# =================================================================
class Settings(BaseSettings):
    """Zentrale Konfiguration mit Pydantic Settings.

    Liest aus .env und bietet typsichere Properties.
    100% rückwärtskompatibel zur alten Struktur.
    """

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
        env_nested_delimiter="__",
    )

    # =================================================================
    # APPLICATION
    # =================================================================
    APP_NAME: str = "pokeys-service"
    APP_ATTRIBUTION: str = "Peter Siebler"
    PROJECT_NAME: str = "hc_smet"
    SERVER_HOST: str = "0.0.0.0"
    SERVER_PORT: int = 8096
    BASE_URL: str = "/"
    FRONTEND_REQUEST_METHOD: str = "GET"

    # =================================================================
    # DIRECTORIES
    # =================================================================
    DATA_DIR: Path = BASE_DIR / "data"
    LOG_DIR: Path = BASE_DIR / "logs"

    # =================================================================
    # DATA MODE
    # =================================================================
    POKEY_SERVICE: str = "POST"
    SENSOR_SCALE_FACTOR: float = 1.0
    FETCH_INTERVAL: int = 300
    STROMPREISE: dict[str, float] = Field(
        default_factory=lambda: {"2026": 0.24}
    )
    CO2_WERT: int = 380
    LIMIT_CLASS_A: int= 100
    LIMIT_CLASS_B: int=150
    LIMIT_CLASS_C: int=200
    LIMIT_CLASS_D: int=300
    LIMIT_CLASS_E: int=400
    LIMIT_CLASS_F: int=500

    # =================================================================
    # DATABASE
    # =================================================================
    DB_ENABLED: bool = False
    DB_PATH: Path = BASE_DIR / "data"
    DATA_LOG_ENABELD: bool = False  # Typo aus .env übernommen für Kompatibilität
    DATA_TRACE_ENABELD: bool = False  # Typo aus .env übernommen für Kompatibilität

    @property
    def database_name(self) -> str:
        """Aktueller Datenbankname basierend auf Jahr"""
        return f"sensors_{datetime.now().year}.db"

    @property
    def database_path(self) -> Path:
        """Validierter, absoluter Pfad zum DB-Verzeichnis"""
        db_path = self.DB_PATH
        if db_path.suffix == ".db" or (db_path.exists() and db_path.is_file()):
            raise RuntimeError(f"DB_PATH must be a directory, got file: {db_path}")
        db_path.mkdir(parents=True, exist_ok=True)
        return db_path.resolve()

    @property
    def analytics_db_path(self) -> Path:
        """Pfad zur analytics.sqlite"""
        env_path = os.getenv("ANALYTICS_DB_PATH")
        if env_path:
            p = Path(env_path)
            return p if p.is_absolute() else (BASE_DIR / p).resolve()
        return self.database_path / "analytics.sqlite"

    # =================================================================
    # ANALYTICS
    # =================================================================
    YEAR_FROM: int = 1970
    YEAR_TO: int = 2100
    ENABLE_CLUSTERING: bool = True
    ENABLE_DAILY_STATS: bool = True

    # =================================================================
    # MQTT
    # =================================================================
    MQTT_ENABLED: bool = False
    MQTT_HOST: str = "localhost"
    MQTT_PORT: int = 1883
    MQTT_CLIENT_ID: str = "pokey_service"
    MQTT_USERNAME: str = ""
    MQTT_PASSWORD: str = ""
    MQTT_INTERVAL: int = 300
    MQTT_TOPIC_TEST: str = ""
    MQTT_TOPIC_BASE: str = "smartmeters"

    @property
    def mqtt_mode(self) -> str:
        """MQTT Modus: 'test' oder 'production'"""
        return "test" if self.MQTT_TOPIC_TEST else "production"

    @property
    def mqtt_topic_sensors(self) -> str:
        """MQTT Topic für Sensoren"""
        return (
            self.MQTT_TOPIC_TEST
            if self.MQTT_TOPIC_TEST
            else f"{self.MQTT_TOPIC_BASE}/sensors"
        )

    # =================================================================
    # HOME ASSISTANT
    # =================================================================
    HA_WEBHOOK_URL: str = ""
    HA_WEBHOOK_ID: str = ""

    # =================================================================
    # SENSOR MAPPING
    # =================================================================
    MAPPING_ENABLED: bool = False
    _MAPPING_FILE: str = "app/domain/house.yaml"

    @property
    def mapping_file(self) -> Path:
        """Absoluter Pfad zur house.yaml"""
        mapping_path = Path(self._MAPPING_FILE)
        if not mapping_path.is_absolute():
            mapping_path = (BASE_DIR / mapping_path).resolve()
        return mapping_path

    # =================================================================
    # LOGGING
    # =================================================================
    LOG_LEVEL: str = "INFO"
    LOG_MODE: str = "both"
    LOG_FILE: str = "logs/app.log"

    # =================================================================
    # POKEYS DEVICES (aus .env gelesen)
    # =================================================================
    POKEYS_DEVICE1_ID: str = "IF64"
    POKEYS_DEVICE1_NAME: str = "poKey64"
    POKEYS_DEVICE1_IP: str = "10.1.1.64"
    POKEYS_DEVICE1_SENSORS: str = "1-25"
    POKEYS_DEVICE1_PINS: str = Field(
        default="0,1,4,5,8,10,14,15,18,19,20,21,22,23,24,25,26,27,40,41,42,43,45,47,48"
    )

    POKEYS_DEVICE2_ID: str = "IF65"
    POKEYS_DEVICE2_NAME: str = "poKey65"
    POKEYS_DEVICE2_IP: str = "10.1.1.65"
    POKEYS_DEVICE2_SENSORS: str = "26-50"
    POKEYS_DEVICE2_PINS: str = Field(
        default="0,1,4,5,8,10,14,15,18,19,20,21,22,23,24,25,26,27,40,41,42,43,45,47,48"
    )

    SENSOR_PER_DEVICE: int = 25

    # =================================================================
    # STRUCTURED MODELS (werden aus .env gebaut)
    # =================================================================
    devices: list[PokeyDevice] = Field(default_factory=list)
    device: DeviceConfig = Field(default_factory=DeviceConfig)

    @model_validator(mode="after")
    def build_devices_from_env(self) -> Settings:
        """Baut PokeyDevice-Liste aus flachen ENV-Variablen"""
        if not self.devices:  # Nur wenn nicht bereits gesetzt
            self.devices = [
                PokeyDevice(
                    id=self.POKEYS_DEVICE1_ID,
                    name=self.POKEYS_DEVICE1_NAME,
                    ip=self.POKEYS_DEVICE1_IP,
                    sensors=self.POKEYS_DEVICE1_SENSORS,
                ),
                PokeyDevice(
                    id=self.POKEYS_DEVICE2_ID,
                    name=self.POKEYS_DEVICE2_NAME,
                    ip=self.POKEYS_DEVICE2_IP,
                    sensors=self.POKEYS_DEVICE2_SENSORS,
                ),
            ]
        return self

    # =================================================================
    # BACKWARD COMPATIBILITY PROPERTIES
    # =================================================================
    @property
    def pokeys_device1_get(self) -> str:
        """Legacy: GET URL für Device 1"""
        return f"http://{self.POKEYS_DEVICE1_IP}/sensorList.json"

    @property
    def pokeys_device2_get(self) -> str:
        """Legacy: GET URL für Device 2"""
        return f"http://{self.POKEYS_DEVICE2_IP}/sensorList.json"

    @cached_property
    def sensor_devices(self) -> dict[str, dict[str, Any]]:
        """Legacy-kompatibles Dictionary für Sensor-Devices.

        Returns:
            {
                "pokey64": {
                    "id": "IF64",
                    "name": "poKey64",
                    "ip": "10.1.1.64",
                    "geturl": "http://10.1.1.64/sensorList.json",
                    "start_index": 1,
                    "sensors": ["IF64:S01", "IF64:S02", ...]
                },
                ...
            }
        """
        result = {}
        for dev in self.devices:
            sensor_start = 1
            if "-" in dev.sensors:
                sensor_start = int(dev.sensors.split("-")[0])

            result[dev.name.lower()] = {
                "id": dev.id,
                "name": dev.name,
                "ip": dev.ip,
                "geturl": dev.sensor_url,
                "start_index": sensor_start,
                "sensors": dev.sensor_list,
            }
        return result

    def get_device(self, name: str) -> dict[str, Any] | None:
        """Holt Device-Config nach Name"""
        return self.sensor_devices.get(name.lower())

    def get_devices_start_index(self, name: str) -> int:
        """Holt Start-Index für Device"""
        dev = self.get_device(name)
        return dev.get("start_index", 1) if dev else 1

    @property
    def ip_addresses(self) -> list[str]:
        """Liste aller Device-IPs"""
        return [d.ip for d in self.devices]

    # =================================================================
    # TIMESTAMP HELPERS
    # =================================================================
    @staticmethod
    def get_timestamp_iso(ts: Any = None) -> str:
        """Konvertiert Timestamp zu ISO-String (UTC)"""
        try:
            if ts is None:
                dt = datetime.now(timezone.utc)
            elif isinstance(ts, datetime):
                dt = ts
            elif isinstance(ts, (int, float)) or str(ts).isdigit():
                ts = float(ts)
                dt = datetime.fromtimestamp(
                    ts / 1000 if ts > 1e12 else ts,
                    tz=timezone.utc,
                )
            else:
                s = str(ts).replace("Z", "+00:00")
                dt = datetime.fromisoformat(s)
        except (ValueError, TypeError):
            dt = datetime.now(timezone.utc)
        return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")


# =================================================================
# SINGLETON
# =================================================================
@lru_cache
def get_settings() -> Settings:
    """Singleton Factory für Settings"""
    return Settings()


settings = get_settings()
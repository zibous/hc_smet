# -*- coding: utf-8 -*-
"""
Zentrale Konfiguration für home-miscale.
Alle Werte aus .env mit sinnvollen Defaults.
"""

import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def _env(key: str, default: str = "") -> str:
    return os.getenv(key, default)


def _env_int(key: str, default: int = 0) -> int:
    return int(os.getenv(key, str(default)))


@dataclass(frozen=True)
class WebhookConfig:
    url: str = _env("HA_WEBHOOK_URL", "")
    id: str = _env("HA_WEBHOOK_ID", "")
    timeout: int = _env_int("HA_WEBHOOK_TIMEOUT", 5)


@dataclass(frozen=True)
class MqttConfig:
    host: str = _env("MQTT_HOST", "10.1.1.119")
    port: int = _env_int("MQTT_PORT", 1883)
    client: str = _env("MQTT_CLIENT", "smdmiscale")
    user: str = _env("MQTT_USER", "")
    password: str = _env("MQTT_PASS", "")
    keepalive: int = _env_int("MQTT_KEEPALIVE", 60)
    topic: str = _env("MQTT_TOPIC", "bodyscale/data")
    statetopic: str = _env("MQTT_STATETOPIC", "bodyscale/status")
    lwt: str = _env("MQTT_LWT", "bodyscale/LWT")
    heartbeat: str = _env("MQTT_HEARTBEAT", "bodyscale/heartbeat")
    ha_topic: str = _env("MQTT_HATOPIC", "homeassistant")
    ha_prefix: str = _env("HAPREFIX", "miscale")


@dataclass(frozen=True)
class LogConfig:
    level: str = _env("LOG_LEVEL", "INFO")
    mode: str = _env("LOG_MODE", "console")
    file: str = _env("LOG_FILE", "logs/miscale.log")
    max_bytes: int = _env_int("LOG_MAX_BYTES", 1_000_000)
    backup_count: int = _env_int("LOG_BACKUP_COUNT", 3)


@dataclass(frozen=True)
class AppConfig:
    """Gesamte App-Konfiguration."""

    app_name: str = _env("APP_NAME", "home-miscale")
    app_version: str = _env("APP_VERSION", "2.1.0")
    host: str = _env("HOST", "0.0.0.0")
    port: int = _env_int("PORT", 5056)
    language: str = _env("LANGUAGE", "de")
    app_title: str = _env("APP_TITLE", "⚖ MiScale")
    data_dir: str = _env("DATA_DIR", str(PROJECT_ROOT / "data"))
    db_path: str = _env("DB_PATH", str(PROJECT_ROOT / "data" / "miscaledata.db"))

    mqtt: MqttConfig = field(default_factory=MqttConfig)
    log: LogConfig = field(default_factory=LogConfig)
    webhook: WebhookConfig = field(default_factory=WebhookConfig)

    # Sprachdaten (aus config/lang/{language}.yaml)
    body_scale_types: tuple = field(default_factory=tuple)
    diff_text: tuple = field(default_factory=tuple)

    def __post_init__(self):
        # Frozen dataclass workaround: object.__setattr__
        import yaml

        lang_file = PROJECT_ROOT / "config" / "lang" / f"{self.language}.yaml"
        if lang_file.exists():
            with open(lang_file, "r", encoding="utf-8") as f:
                lang = yaml.safe_load(f) or {}
            object.__setattr__(self, "body_scale_types", tuple(lang.get("body_scale_types", [])))
            dt = lang.get("diff_text", {})
            object.__setattr__(self, "diff_text", (dt.get("down", ""), dt.get("same", ""), dt.get("up", "")))
        else:
            object.__setattr__(
                self,
                "body_scale_types",
                (
                    "Fettleibig",
                    "Übergewichtig",
                    "Dick",
                    "Bewegungsmangel",
                    "Ausgeglichen",
                    "Ausgeglichen Muskulös",
                    "Dünn",
                    "Ausgeglichen Dünn",
                    "Dünn Muskulös",
                ),
            )
            object.__setattr__(self, "diff_text", ("Abgenommen", "Keine Veränderung", "Zugenommen"))


# Singleton
cfg = AppConfig()


# Date helpers
_DATEFORMAT_TS = "%Y-%m-%dT%H:%M:%S"


def getTimestamp() -> str:
    return datetime.now().strftime(_DATEFORMAT_TS)

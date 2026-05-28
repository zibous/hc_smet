# -*- coding: utf-8 -*-
"""Home Assistant MQTT Auto-Discovery für MiScale Sensoren.

Sensor-Definitionen kommen aus config/ha_discovery.yaml.
"""

import logging

import yaml

from app.core.config import PROJECT_ROOT, cfg
from app.core.mqtt import MqttClient

log = logging.getLogger(__name__)

_DISCOVERY_FILE = PROJECT_ROOT / "config" / "ha_discovery.yaml"
_config: dict = {}


def _load_config() -> dict:
    global _config
    if _config:
        return _config
    if _DISCOVERY_FILE.exists():
        with open(_DISCOVERY_FILE, "r", encoding="utf-8") as f:
            _config = yaml.safe_load(f) or {}
    else:
        log.warning("ha_discovery.yaml nicht gefunden: %s", _DISCOVERY_FILE)
    return _config


def _device_block(user_name: str) -> dict:
    config = _load_config()
    device = config.get("device", {})
    return {
        "identifiers": [f"{cfg.mqtt.ha_prefix}_{user_name.lower()}"],
        "name": f"MiScale {user_name}",
        "model": device.get("model", "Mi Body Composition Scale 2"),
        "manufacturer": device.get("manufacturer", "Xiaomi"),
        "sw_version": cfg.app_version,
    }


def publish_discovery(mqtt_client: MqttClient, user_name: str):
    """Publiziert alle HA Discovery Configs für einen User."""
    if not mqtt_client or not mqtt_client.ready:
        return

    config = _load_config()
    sensors = config.get("sensors", [])
    ha_base = cfg.mqtt.ha_topic
    prefix = cfg.mqtt.ha_prefix
    count = 0

    for sensor in sensors:
        key = sensor["key"]
        topic_type = sensor.get("topic", "data")
        state_topic = f"{cfg.mqtt.topic}/{user_name}/{topic_type}"

        uid = f"{prefix}_{user_name.lower()}_{key}"
        discovery_topic = f"{ha_base}/sensor/{uid}/config"

        payload = {
            "name": f"{user_name} {sensor['name']}",
            "unique_id": uid,
            "object_id": uid,
            "state_topic": state_topic,
            "value_template": f"{{{{ value_json.{key} }}}}",
            "icon": sensor.get("icon", ""),
            "device": _device_block(user_name),
        }

        if sensor.get("unit"):
            payload["unit_of_measurement"] = sensor["unit"]
        if sensor.get("device_class"):
            payload["device_class"] = sensor["device_class"]
        if sensor.get("state_class"):
            payload["state_class"] = sensor["state_class"]
        if sensor.get("json_attributes"):
            payload["json_attributes_topic"] = state_topic

        if mqtt_client.publish(discovery_topic, payload, retain=True):
            count += 1

    log.info("HA Discovery: %d Sensoren publiziert für %s", count, user_name)


def publish_discovery_all(mqtt_client: MqttClient, user_names: list[str]):
    """Publiziert Discovery für alle User."""
    for name in user_names:
        publish_discovery(mqtt_client, name)

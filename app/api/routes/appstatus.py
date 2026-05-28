# -*- coding: utf-8 -*-
"""App Status Route für das Übersichtsdashboard."""

from fastapi import APIRouter

from app.core.config import cfg
from app.core.mqtt import MqttClient

router = APIRouter()

_mqtt: MqttClient | None = None


def init_appstatus(mqtt_client: MqttClient):
    global _mqtt
    _mqtt = mqtt_client


@router.get("/appstatus")
async def appstatus():
    return {
        "app": cfg.app_name,
        "version": cfg.app_version,
        "status": "ok",
        "port": cfg.port,
        "mqtt": {
            "broker": cfg.mqtt.host,
            "port": cfg.mqtt.port,
            "connected": _mqtt.ready if _mqtt else False,
        },
    }

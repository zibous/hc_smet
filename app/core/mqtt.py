# -*- coding: utf-8 -*-
"""MQTT Client für home-miscale (paho-mqtt 2.x).

Wartet beim Start auf den Broker (Retry mit Backoff).
Reconnect bei Publish-Fehlern – App läuft auch ohne MQTT weiter.
"""

import json
import logging
import socket
import time

import paho.mqtt.publish as publish

from app.core.config import cfg

log = logging.getLogger(__name__)

MAX_RETRIES = 5
INITIAL_BACKOFF = 2


class MqttClient:
    """Publisht Nachrichten an den MQTT Broker."""

    def __init__(self):
        mc = cfg.mqtt
        self.host = mc.host
        self.port = mc.port
        self.client_id = mc.client
        self.keepalive = mc.keepalive
        self.auth: dict[str, str] | None = None
        if mc.user and mc.password:
            self.auth = {"username": mc.user, "password": mc.password}
        self.ready = self._wait_for_broker() if self.host else False

    def _check_connection(self) -> bool:
        try:
            s = socket.create_connection((self.host, self.port), timeout=3)
            s.close()
            return True
        except (OSError, socket.timeout):
            return False

    def _wait_for_broker(self) -> bool:
        for attempt in range(1, MAX_RETRIES + 1):
            if self._check_connection():
                log.info("MQTT Broker erreichbar: %s:%s (Versuch %d)", self.host, self.port, attempt)
                return True
            wait = INITIAL_BACKOFF * (2 ** (attempt - 1))
            log.info("MQTT Broker nicht erreichbar – Versuch %d/%d, nächster in %ds", attempt, MAX_RETRIES, wait)
            time.sleep(wait)
        log.warning("MQTT Broker nicht erreichbar nach %d Versuchen – App läuft ohne MQTT", MAX_RETRIES)
        return False

    def _reconnect(self) -> bool:
        if self._check_connection():
            self.ready = True
            log.info("MQTT Broker wieder erreichbar")
            return True
        return False

    def publish(self, topic: str, payload=None, retain: bool = False, qos: int = 0, **kwargs) -> bool:
        if not self.host:
            return False
        if not self.ready:
            if not self._reconnect():
                return False

        topic = kwargs.get("topic", topic) or topic
        payload = kwargs.get("payload", payload) or payload
        retain = kwargs.get("retain", retain)

        if isinstance(payload, dict):
            payload = json.dumps(payload)

        try:
            publish.single(
                topic,
                payload=payload,
                qos=qos,
                retain=retain,
                hostname=self.host,
                port=self.port,
                client_id=self.client_id,
                keepalive=self.keepalive,
                auth=self.auth,
            )
            log.debug("MQTT → %s", topic)
            return True
        except Exception:
            log.exception("MQTT publish fehlgeschlagen: %s", topic)
            self.ready = False
            return False

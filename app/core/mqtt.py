# -*- coding: utf-8 -*-

import socket
import os
import json
from typing import Union, Any
import paho.mqtt.publish as publish

import logging
logger = logging.getLogger(__name__)


class MQTTClient:
    """MQTT Client für Home Assistant Integration"""

    def __init__(
        self,
        host="localhost",
        port=1883,
        client_id="pytoncli",
        username=None,
        password=None,
        qos=0,
        retain=True,
        keepalive=60
    ):
        self.host = host
        self.port = port
        self.client_id = client_id
        self.qos = qos
        self.retain = retain
        self.keepalive = keepalive

        self.username = username
        self.passwort = password

        # Authentifizierung vorbereiten
        self.auth: Any = None
        if username:
            self.auth = {"username": username, "password": password or ""}

    # ---------------------------------------------------------
    # Sichere Publish-Methode: True bei Erfolg, False bei Fehler
    # ---------------------------------------------------------
    def publish_safe(self, topic: str, payload: str) -> bool:
        """
        Sendet eine MQTT-Nachricht sicher.
        Gibt True zurück, wenn Publish erfolgreich war,
        sonst False (Fehler wird geloggt).
        """
        try:
            publish.single(
                topic=topic,
                payload=payload,
                qos=self.qos,
                retain=self.retain,
                hostname=self.host,
                port=self.port,
                client_id=self.client_id,
                keepalive=self.keepalive,
                auth=self.auth,
            )
            return True
        except Exception as e:
            logger.error(f"MQTT Publish Fehler ({topic}): {e} für {self.host}:{self.port}, User {self.username}" )
            return False

    # ---------------------------------------------------------
    # Komfort-Methoden
    # ---------------------------------------------------------
    def publish(self, topic: str, payload: Union[str, dict, list], retain: bool = False) -> bool:
        """Publish JSON-String."""
        self.retain = retain
        if not isinstance(payload, str):
            payload = json.dumps(payload)
        return self.publish_safe(topic, payload)

    def publish_value(self, topic: str, value, retain: bool = False) -> bool:
        """Publish einfacher Wert (wird zu String)."""
        self.retain = retain
        return self.publish_safe(topic, str(value))

    def publish_error(self, topic: str, message: str) -> bool:
        """Publish Fehlermeldung."""
        self.retain = False
        return self.publish_value("error", message)

    # ---------------------------------------------------------
    # Broker erreichbar?
    # ---------------------------------------------------------
    def is_connected(self) -> bool:
        """
        Prüft, ob der MQTT-Broker erreichbar ist.
        Belastet den Broker NICHT, da nur ein TCP-Porttest erfolgt.
        """
        try:
            with socket.create_connection((self.host, self.port), timeout=2):
                return True
        except OSError:
            return False

    def save_payload(self, payload: str, folder: str = "./data") -> bool:
        """
        Speichert einen JSON-Payload formatiert (pretty printed) im angegebenen Ordner.
        Gibt (success: bool zurück.
        """

        # Ordner erstellen, falls nicht vorhanden
        os.makedirs(folder, exist_ok=True)

        # Dateiname mit Timestamp
        filename = "payload.json"
        filepath = os.path.join(folder, filename)

        try:
            # JSON validieren und formatiert speichern
            parsed = json.loads(payload)
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(parsed, f, indent=4, ensure_ascii=False)
            return True

        except Exception as _:
            # Fehlerfall: Datei trotzdem speichern, aber als RAW
            fallback = filepath.replace(".json", "_raw.json")
            try:
                with open(fallback, "w", encoding="utf-8") as f:
                    f.write(payload)
                return False
            except:
                # Wenn selbst das schiefgeht
                return False

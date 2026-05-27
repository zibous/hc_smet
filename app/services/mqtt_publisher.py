# -*- coding: utf-8 -*-
"""MQTT Publisher für Home Assistant.

Publiziert Sensor-, Raum-, Bereichs- und Haus-Daten periodisch via MQTT.
Nutzt den SensorStore (RAM) für aktuelle Werte und hourly_values (DB) für Tagesverbrauch.

Features:
- Periodisches Publishing (MQTT_INTERVAL aus .env)
- LWT (Last Will and Testament): Online/Offline Status
- Heartbeat mit System-Health-Daten
- Hierarchische Topics: sensors/S01, rooms/EG_R01, areas/EG, home
"""

import json
import logging
import time
import threading
from datetime import datetime, timezone, timedelta
from typing import Any

import paho.mqtt.client as mqtt

from app.core.app_config import settings
from app.infrastructure.database.dbconnect import Database
import app.domain.house as house

logger = logging.getLogger(__name__)

STRUCTURE = house.STRUCTURE


class MQTTPublisher:
    """MQTT Publisher mit LWT, Heartbeat und periodischem Sensor-Publishing."""

    def __init__(self, sensor_store):
        self.store = sensor_store
        self._is_pokeys_manager = hasattr(sensor_store, "get_all_data")
        self.client: mqtt.Client | None = None
        self.connected = False
        self._timer: threading.Timer | None = None
        self._base_topic = settings.MQTT_TOPIC_BASE

    # =========================================================
    # CONNECTION
    # =========================================================
    def start(self):

        """Verbindet zum MQTT Broker und startet den periodischen Publisher."""
        if not settings.MQTT_ENABLED:
            logger.info("MQTT ist deaktiviert (MQTT_ENABLED=false).")
            return

        try:
            self.client = mqtt.Client(
                client_id=settings.MQTT_CLIENT_ID,
                protocol=mqtt.MQTTv5
            )

            # Authentifizierung
            if settings.MQTT_USERNAME:
                self.client.username_pw_set(settings.MQTT_USERNAME, settings.MQTT_PASSWORD)

            # LWT (Last Will and Testament) — wird gesendet wenn Verbindung abbricht
            lwt_topic = f"{self._base_topic}/status"
            self.client.will_set(lwt_topic, payload="offline", qos=1, retain=True)

            # Callbacks
            self.client.on_connect = self._on_connect
            self.client.on_disconnect = self._on_disconnect

            # Verbinden
            self.client.connect(settings.MQTT_HOST, settings.MQTT_PORT, keepalive=60)
            self.client.loop_start()

            logger.info(f"MQTT Publisher gestartet: {settings.MQTT_HOST}:{settings.MQTT_PORT}")

        except Exception as e:
            logger.error(f"❌ MQTT Verbindung fehlgeschlagen: {e}")

    def stop(self):
        """Trennt die MQTT-Verbindung sauber."""
        if self._timer:
            self._timer.cancel()

        if self.client and self.connected:
            # Offline-Status senden
            self.client.publish(f"{self._base_topic}/status", "offline", qos=1, retain=True)
            self.client.loop_stop()
            self.client.disconnect()
            logger.info("MQTT Publisher gestoppt.")

    # =========================================================
    # CALLBACKS
    # =========================================================
    def _on_connect(self, client, userdata, flags, rc, properties=None):
        """Wird aufgerufen wenn die Verbindung steht."""
        self.connected = True
        # Online-Status senden
        client.publish(f"{self._base_topic}/status", "online", qos=1, retain=True)
        logger.info(f"✅ MQTT verbunden. Topic-Base: {self._base_topic}")

        # Home Assistant Discovery publizieren
        self.publish_discovery()

        # Ersten Publish-Zyklus starten
        self._schedule_publish()

    def _on_disconnect(self, client, userdata, rc, properties=None):
        """Wird aufgerufen wenn die Verbindung getrennt wird."""
        self.connected = False
        logger.warning(f"⚠️ MQTT Verbindung getrennt (rc={rc}).")

    # =========================================================
    # PERIODIC PUBLISHING
    # =========================================================
    def _schedule_publish(self):
        """Plant den nächsten Publish-Zyklus."""
        if self._timer:
            self._timer.cancel()
        self._timer = threading.Timer(settings.MQTT_INTERVAL, self._publish_cycle)
        self._timer.daemon = True
        self._timer.start()

    def _publish_cycle(self):
        """Führt einen kompletten Publish-Zyklus aus."""
        if not self.connected:
            self._schedule_publish()
            return

        try:
            self._publish_heartbeat()
            self._publish_sensors()
            self._publish_rooms()
            self._publish_areas()
            self._publish_home()

        except Exception as e:
            logger.error(f"❌ MQTT Publish-Zyklus fehlgeschlagen: {e}")

        # Nächsten Zyklus planen
        self._schedule_publish()

    # =========================================================
    # HEARTBEAT (System Health)
    # =========================================================
    def _publish_heartbeat(self):
        """Publiziert System-Health als Heartbeat."""
        from app.api.settingsdata import get_system_health

        health = get_system_health()
        self.client.publish(
            f"{self._base_topic}/heartbeat",
            json.dumps(health),
            qos=0,
            retain=True
        )

    # =========================================================
    # SENSOR PUBLISHING
    # =========================================================
    def _publish_sensors(self):
        """Publiziert alle aktiven Sensoren."""
        sensors_info = STRUCTURE.get("sensors", {})
        rooms_info = STRUCTURE.get("rooms", {})

        if self._is_pokeys_manager:
            # GET-Modus: Daten vom PoKeysManager
            all_data = self.store.get_all_data()
            for sensor_id, info in all_data.items():
                if info.get("total_kwh", 0) == 0:
                    continue

                meta = sensors_info.get(sensor_id, {})
                room_id = meta.get("room", "")
                room_name = rooms_info.get(room_id, {}).get("name", "-")

                # Tagesverbrauch aus DB
                day_consumption = self._get_day_consumption(sensor_id)

                payload = {
                    "id": sensor_id,
                    "name": info.get("name", sensor_id),
                    "room": room_name,
                    "total": round(info.get("total_kwh", 0), 2),
                    "current": round(info.get("verbrauch_kwh", 0), 4),
                    "watt": info.get("watt", 0),
                    "day": round(day_consumption, 3),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "attribution": settings.APP_ATTRIBUTION,
                    "source": settings.APP_NAME,
                }

                topic = f"{self._base_topic}/sensors/{sensor_id}"
                self.client.publish(topic, json.dumps(payload), qos=0, retain=True)
        else:
            # POST-Modus: Legacy SensorStore
            store_data = self.store.get_all()
            for sensor_id, entry in store_data.items():
                if entry.current == 0:
                    continue

                meta = sensors_info.get(sensor_id, {})
                room_id = meta.get("room", "")
                room_name = rooms_info.get(room_id, {}).get("name", "-")

                # Tagesverbrauch aus DB
                day_consumption = self._get_day_consumption(sensor_id)

                payload = {
                    "id": sensor_id,
                    "name": meta.get("name", sensor_id),
                    "room": room_name,
                    "total": round(entry.current * settings.SENSOR_SCALE_FACTOR, 2),
                    "current": round(entry.delta * settings.SENSOR_SCALE_FACTOR, 4),
                    "day": round(day_consumption, 3),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "attribution": settings.APP_ATTRIBUTION,
                    "source": settings.APP_NAME,
                }

                topic = f"{self._base_topic}/sensors/{sensor_id}"
                self.client.publish(topic, json.dumps(payload), qos=0, retain=True)

    def _publish_rooms(self):
        """Publiziert Raum-Aggregationen."""
        rooms_info = STRUCTURE.get("rooms", {})
        sensors_info = STRUCTURE.get("sensors", {})

        for room_id, room in rooms_info.items():
            sensor_ids = [sid for sid, s in sensors_info.items() if s.get("room") == room_id]
            day_total = sum(self._get_day_consumption(sid) for sid in sensor_ids)

            current_total = 0.0
            if self._is_pokeys_manager:
                all_data = self.store.get_all_data()
                current_total = sum(
                    all_data[sid].get("verbrauch_kwh", 0)
                    for sid in sensor_ids if sid in all_data
                )
            else:
                store_data = self.store.get_all()
                current_total = sum(
                    store_data[sid].delta * settings.SENSOR_SCALE_FACTOR
                    for sid in sensor_ids if sid in store_data
                )

            if day_total == 0 and current_total == 0:
                continue

            payload = {
                "id": room_id,
                "name": room["name"],
                "type": "room",
                "area": room.get("area", ""),
                "day": round(day_total, 3),
                "current": round(current_total, 4),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

            topic = f"{self._base_topic}/rooms/{room_id}"
            self.client.publish(topic, json.dumps(payload), qos=0, retain=True)

    def _publish_areas(self):
        """Publiziert Bereichs-Aggregationen."""
        areas_info = STRUCTURE.get("areas", {})
        rooms_info = STRUCTURE.get("rooms", {})
        sensors_info = STRUCTURE.get("sensors", {})

        for area_id, area in areas_info.items():
            room_ids = [rid for rid, r in rooms_info.items() if r.get("area") == area_id]
            sensor_ids = [sid for sid, s in sensors_info.items() if s.get("room") in room_ids]
            day_total = sum(self._get_day_consumption(sid) for sid in sensor_ids)

            if day_total == 0:
                continue

            payload = {
                "id": area_id,
                "name": area["name"],
                "type": "area",
                "day": round(day_total, 3),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

            topic = f"{self._base_topic}/areas/{area_id}"
            self.client.publish(topic, json.dumps(payload), qos=0, retain=True)

    def _publish_home(self):
        """Publiziert Haus-Gesamtverbrauch."""
        sensors_info = STRUCTURE.get("sensors", {})
        day_total = sum(self._get_day_consumption(sid) for sid in sensors_info.keys())

        payload = {
            "id": "HOME",
            "name": "Haus",
            "type": "home",
            "day": round(day_total, 3),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        topic = f"{self._base_topic}/home"
        self.client.publish(topic, json.dumps(payload), qos=0, retain=True)

    # =========================================================
    # HOME ASSISTANT DISCOVERY
    # =========================================================
    def publish_discovery(self):
        """Publiziert Home Assistant MQTT Discovery Messages mit Hierarchie."""
        if not self.connected:
            logger.warning("MQTT nicht verbunden - Discovery übersprungen")
            return

        sensors_info = STRUCTURE.get("sensors", {})
        rooms_info = STRUCTURE.get("rooms", {})
        areas_info = STRUCTURE.get("areas", {})

        # Device Config aus settings
        device_config = settings.device

        # 1. Haus-Gerät mit Area-Entities
        house_device = {
            "identifiers": [device_config.device_id],
            "name": device_config.name,
            "model": device_config.model,
            "manufacturer": device_config.manufacturer,
            "sw_version": device_config.firmware,
        }

        # Haus Gesamt Entity
        config = {
            "name": "Verbrauch Haus",
            "unique_id": "smartmeter_home",
            "state_topic": f"{self._base_topic}/home",
            "unit_of_measurement": "kWh",
            "device_class": "energy",
            "state_class": "total",
            "value_template": "{{ value_json.day }}",
            "json_attributes_topic": f"{self._base_topic}/home",
            "device": house_device,
        }
        self.client.publish(
            "homeassistant/sensor/smartmeter/home/config",
            json.dumps(config),
            qos=1,
            retain=True
        )

        # Areas als Entities unter Haus-Gerät
        for area_id, area in areas_info.items():
            config = {
                "name": f"Verbrauch {area['name']}",
                "unique_id": f"smartmeter_area_{area_id}",
                "state_topic": f"{self._base_topic}/areas/{area_id}",
                "unit_of_measurement": "kWh",
                "device_class": "energy",
                "state_class": "total",
                "value_template": "{{ value_json.day }}",
                "json_attributes_topic": f"{self._base_topic}/areas/{area_id}",
                "device": house_device,
            }
            self.client.publish(
                f"homeassistant/sensor/smartmeter/area_{area_id}/config",
                json.dumps(config),
                qos=1,
                retain=True
            )

        # 2. Area-Geräte mit Raum-Entities
        for area_id, area in areas_info.items():
            area_device = {
                "identifiers": [f"smartmeter_area_{area_id}"],
                "name": f"Verbrauch {area['name']}",
                "model": "Area Aggregation",
                "manufacturer": device_config.manufacturer,
                "via_device": device_config.device_id,
            }

            # Räume als Entities unter Area-Gerät
            room_ids = [rid for rid, r in rooms_info.items() if r.get("area") == area_id]
            for room_id in room_ids:
                room = rooms_info[room_id]
                config = {
                    "name": f"Verbrauch {room['name']}",
                    "unique_id": f"smartmeter_room_{room_id}",
                    "state_topic": f"{self._base_topic}/rooms/{room_id}",
                    "unit_of_measurement": "kWh",
                    "device_class": "energy",
                    "state_class": "total",
                    "value_template": "{{ value_json.day }}",
                    "json_attributes_topic": f"{self._base_topic}/rooms/{room_id}",
                    "device": area_device,
                }
                self.client.publish(
                    f"homeassistant/sensor/smartmeter/room_{room_id}/config",
                    json.dumps(config),
                    qos=1,
                    retain=True
                )

        # 3. Raum-Geräte mit Sensor-Entities
        for room_id, room in rooms_info.items():
            area_id = room.get("area", "")
            room_device = {
                "identifiers": [f"smartmeter_room_{room_id}"],
                "name": f"Verbrauch {room['name']}",
                "model": "Room Aggregation",
                "manufacturer": device_config.manufacturer,
                "via_device": f"smartmeter_area_{area_id}",
            }

            # Sensoren als Entities unter Raum-Gerät
            sensor_ids = [sid for sid, s in sensors_info.items() if s.get("room") == room_id]
            for sensor_id in sensor_ids:
                sensor = sensors_info[sensor_id]
                config = {
                    "name": sensor.get("name", sensor_id),
                    "unique_id": f"smartmeter_{sensor_id}",
                    "state_topic": f"{self._base_topic}/sensors/{sensor_id}",
                    "unit_of_measurement": "kWh",
                    "device_class": "energy",
                    "state_class": "total",
                    "value_template": "{{ value_json.day }}",
                    "json_attributes_topic": f"{self._base_topic}/sensors/{sensor_id}",
                    "device": {
                        "identifiers": [f"smartmeter_room_{room_id}"],
                        "name": f"Verbrauch {room['name']}",
                        "model": "Room Aggregation",
                        "manufacturer": device_config.manufacturer,
                        "via_device": f"smartmeter_area_{area_id}",
                    },
                }
                self.client.publish(
                    f"homeassistant/sensor/smartmeter/{sensor_id}/config",
                    json.dumps(config),
                    qos=1,
                    retain=True
                )

        logger.info("✅ Home Assistant Discovery Messages publiziert")

    def unpublish_discovery(self):
        """Löscht alte Home Assistant MQTT Discovery Messages."""
        if not self.connected:
            logger.warning("MQTT nicht verbunden - Unpublish übersprungen")
            return

        sensors_info = STRUCTURE.get("sensors", {})
        rooms_info = STRUCTURE.get("rooms", {})
        areas_info = STRUCTURE.get("areas", {})

        # Sensoren
        for sensor_id in sensors_info.keys():
            topic = f"homeassistant/sensor/smartmeter/{sensor_id}/config"
            self.client.publish(topic, "", qos=1, retain=True)

        # Räume
        for room_id in rooms_info.keys():
            topic = f"homeassistant/sensor/smartmeter/room_{room_id}/config"
            self.client.publish(topic, "", qos=1, retain=True)

        # Bereiche
        for area_id in areas_info.keys():
            topic = f"homeassistant/sensor/smartmeter/area_{area_id}/config"
            self.client.publish(topic, "", qos=1, retain=True)

        # Haus
        topic = "homeassistant/sensor/smartmeter/home/config"
        self.client.publish(topic, "", qos=1, retain=True)

        logger.info("✅ Home Assistant Discovery Messages gelöscht")

    # =========================================================
    # HELPER
    # =========================================================
    def _get_day_consumption(self, sensor_id: str) -> float:
        """Holt den Tagesverbrauch aus hourly_values (ab 00:00 UTC heute)."""
        if Database._instance is None:
            return 0.0

        today_start = int(datetime.now(timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        ).timestamp())

        try:
            year = datetime.now(timezone.utc).year
            conn = Database._instance.get_conn(year=year)
            row = conn.execute(
                "SELECT COALESCE(SUM(consumption), 0) FROM hourly_values WHERE sensor_id = ? AND hour >= ?",
                (sensor_id, today_start)
            ).fetchone()
            conn.close()
            return row[0] if row else 0.0
        except Exception:
            return 0.0

# -*- coding: utf-8 -*-
"""Webhook-Integration für Home Assistant.

Sendet periodisch System-Health-Daten an einen konfigurierten Webhook-Endpoint.
Optional — nur aktiv wenn HA_WEBHOOK_URL und HA_WEBHOOK_ID in der .env gesetzt sind.
"""

import logging
import threading
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import requests

from app.core.app_config import settings

logger = logging.getLogger(__name__)


class Webhook:
    """HTTP Webhook Client."""

    def __init__(self, base_url: str, webhook_id: str, timeout: int = 5):
        self.base_url = base_url.rstrip("/")
        self.webhook_id = webhook_id
        self.timeout = timeout

    @property
    def url(self) -> str:
        return f"{self.base_url}/api/webhook/{self.webhook_id}"

    def send(self, data: Optional[Dict[str, Any]] = None) -> bool:
        try:
            response = requests.post(
                self.url,
                json=data or {},
                timeout=self.timeout
            )
            response.raise_for_status()
            return True
        except requests.RequestException as e:
            logger.debug(f"Webhook send failed: {e}")
            return False


class WebhookPublisher:
    """Periodischer Webhook Publisher für System-Health-Daten.

    Sendet alle MQTT_INTERVAL Sekunden die System-Health an Home Assistant.
    Nutzt den gleichen Intervall wie MQTT (da beide HA-Integrationen sind).
    """

    def __init__(self):
        self._webhook: Optional[Webhook] = None
        self._timer: Optional[threading.Timer] = None
        self._interval = settings.MQTT_INTERVAL  # Gleicher Intervall wie MQTT

    def start(self):
        """Startet den periodischen Webhook-Publisher."""
        url = getattr(settings, "HA_WEBHOOK_URL", "") or ""
        wid = getattr(settings, "HA_WEBHOOK_ID", "") or ""

        if not url or not wid:
            logger.info("Webhook ist deaktiviert (HA_WEBHOOK_URL/ID nicht gesetzt).")
            return

        self._webhook = Webhook(base_url=url, webhook_id=wid)
        logger.info(f"✅ Webhook Publisher gestartet: {self._webhook.url} (Intervall: {self._interval}s)")

        # Ersten Zyklus starten
        self._schedule()

    def stop(self):
        """Stoppt den periodischen Publisher."""
        if self._timer:
            self._timer.cancel()
            self._timer = None

    def _schedule(self):
        """Plant den nächsten Webhook-Aufruf."""
        if self._timer:
            self._timer.cancel()
        self._timer = threading.Timer(self._interval, self._publish)
        self._timer.daemon = True
        self._timer.start()

    def _publish(self):
        """Sendet System-Health-Daten an den Webhook."""
        if not self._webhook:
            return

        try:
            from app.api.settingsdata import get_system_health

            health = get_system_health()
            payload = {
                "event": "health_update",
                "application": settings.APP_NAME,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                **health
            }

            ok = self._webhook.send(payload)
            if ok:
                logger.debug("Webhook health_update gesendet.")
        except Exception as e:
            logger.debug(f"Webhook publish fehlgeschlagen: {e}")

        # Nächsten Zyklus planen
        self._schedule()


def notify_ha(event: str, **kwargs) -> bool:
    """Sendet ein einzelnes Event an Home Assistant (wenn konfiguriert).

    Usage:
        notify_ha("app_start", version="2.2.0")
        notify_ha("error", message="Device unreachable", severity="critical")
    """
    url = getattr(settings, "HA_WEBHOOK_URL", "") or ""
    wid = getattr(settings, "HA_WEBHOOK_ID", "") or ""

    if not url or not wid:
        return False

    try:
        wh = Webhook(base_url=url, webhook_id=wid)
        payload: Dict[str, Any] = {
            "event": event,
            "application": settings.APP_NAME,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        payload.update(kwargs)
        return wh.send(payload)
    except Exception as e:
        logger.debug(f"Webhook error: {e}")
        return False

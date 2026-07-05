# -*- coding: utf-8 -*-
"""
Generischer Webhook-Publisher (Standard v2) für hc_smet
========================================================
Heartbeat alle 60s mit Haus-Verbrauch + Geschoss-Aufschlüsselung.
"""

import logging
import threading
import time
from datetime import date, datetime, timezone
from typing import Any, Callable, Dict, Optional

import requests
from pydantic import BaseModel

from app.core.app_config import settings

logger = logging.getLogger(__name__)

APP_ID = "hc_smet"


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
            response = requests.post(self.url, json=data or {}, timeout=self.timeout)
            response.raise_for_status()
            return True
        except requests.RequestException as e:
            logger.debug("Webhook send failed: %s", e)
            return False


class WebhookPublisher:
    """Generischer Publisher. Callbacks liefern Pydantic-Schemas."""

    def __init__(
        self,
        build_heartbeat: Callable[[], BaseModel],
        build_daily: Optional[Callable[[], BaseModel]] = None,
        build_monthly: Optional[Callable[[], BaseModel]] = None,
    ):
        self._webhook: Optional[Webhook] = None
        self._timer: Optional[threading.Timer] = None
        self._running = False
        self._start_time = time.time()
        self._last_day: Optional[str] = None
        self._last_month: Optional[tuple] = None
        self._interval = 60

        self._build_heartbeat = build_heartbeat
        self._build_daily = build_daily
        self._build_monthly = build_monthly

    def start(self):
        url = getattr(settings, "HA_WEBHOOK_URL", "") or ""
        wid = getattr(settings, "HA_WEBHOOK_ID", "") or ""

        if not url.strip() or not wid.strip():
            logger.info("Webhook deaktiviert (HA_WEBHOOK_URL/ID nicht gesetzt)")
            return

        self._webhook = Webhook(base_url=url, webhook_id=wid)
        self._running = True
        self._last_day = date.today().isoformat()
        self._last_month = (date.today().year, date.today().month)

        logger.info("✅ Webhook Publisher gestartet: %s (Intervall: %ds)", self._webhook.url, self._interval)

        # Erster Heartbeat sofort
        self._send_heartbeat()
        self._schedule_next()

    def stop(self):
        self._running = False
        if self._timer:
            self._timer.cancel()
            self._timer = None

    def _schedule_next(self):
        if not self._running:
            return
        self._timer = threading.Timer(self._interval, self._tick)
        self._timer.daemon = True
        self._timer.start()

    def _tick(self):
        if not self._running:
            return
        self._check_day_change()
        self._check_month_change()
        self._send_heartbeat()
        self._schedule_next()

    def _base_payload(self, event: str) -> Dict[str, Any]:
        return {
            "event": event,
            "app_id": APP_ID,
            "version": getattr(settings, "APP_VERSION", ""),
            "ts": datetime.now().isoformat(timespec="seconds"),
        }

    def _send_heartbeat(self):
        if not self._webhook:
            return
        try:
            schema = self._build_heartbeat()
            payload = self._base_payload("heartbeat")
            payload["uptime_s"] = int(time.time() - self._start_time)
            payload["status"] = "ok"
            payload["kpi"] = schema.model_dump()
            self._webhook.send(payload)
        except Exception as e:
            logger.debug("Heartbeat fehlgeschlagen: %s", e)

    def _check_day_change(self):
        today = date.today().isoformat()
        if self._last_day and today != self._last_day and self._build_daily:
            try:
                schema = self._build_daily()
                payload = self._base_payload("daily_summary")
                payload["date"] = self._last_day
                payload["summary"] = schema.model_dump()
                if self._webhook:
                    self._webhook.send(payload)
                logger.info("daily_summary gesendet für %s", self._last_day)
            except Exception as e:
                logger.warning("daily_summary fehlgeschlagen: %s", e)
        self._last_day = today

    def _check_month_change(self):
        now = date.today()
        current_month = (now.year, now.month)
        if self._last_month and current_month != self._last_month and self._build_monthly:
            year, month = self._last_month
            try:
                schema = self._build_monthly()
                payload = self._base_payload("monthly_summary")
                payload["year"] = year
                payload["month"] = month
                payload["summary"] = schema.model_dump()
                if self._webhook:
                    self._webhook.send(payload)
                logger.info("monthly_summary gesendet für %d-%02d", year, month)
            except Exception as e:
                logger.warning("monthly_summary fehlgeschlagen: %s", e)
        self._last_month = current_month


# ══════════════════════════════════════════════════════════════════════
# notify_ha() – für einzelne Events
# ══════════════════════════════════════════════════════════════════════

_webhook: Optional[Webhook] = None
_webhook_checked: bool = False


def _get_webhook() -> Optional[Webhook]:
    global _webhook, _webhook_checked
    if _webhook_checked:
        return _webhook
    _webhook_checked = True
    url = getattr(settings, "HA_WEBHOOK_URL", "") or ""
    wid = getattr(settings, "HA_WEBHOOK_ID", "") or ""
    if url.strip() and wid.strip():
        _webhook = Webhook(base_url=url, webhook_id=wid)
        return _webhook
    return None


def notify_ha(event: str, **kwargs: Any) -> bool:
    """Sendet ein einzelnes Event an Home Assistant."""
    wh = _get_webhook()
    if not wh:
        return False
    try:
        payload: Dict[str, Any] = {
            "event": event,
            "app_id": APP_ID,
            "version": getattr(settings, "APP_VERSION", ""),
            "ts": datetime.now().isoformat(timespec="seconds"),
        }
        payload.update(kwargs)
        ok = wh.send(payload)
        if ok:
            logger.debug("Webhook sent: %s", event)
        return ok
    except Exception as e:
        logger.debug("Webhook error: %s", e)
        return False

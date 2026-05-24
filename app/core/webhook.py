# -*- coding: utf-8 -*-
"""Webhook-Modul für Home Assistant Benachrichtigungen."""

import logging
from typing import Any, Dict, Optional

import requests

from app.core.config import cfg, getTimestamp

log = logging.getLogger(__name__)


class Webhook:
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
            log.debug("Webhook send failed: %s", e)
            return False


_webhook: Optional[Webhook] = None


def _get_webhook() -> Optional[Webhook]:
    global _webhook
    if _webhook is not None:
        return _webhook
    if cfg.webhook.url and cfg.webhook.id:
        _webhook = Webhook(cfg.webhook.url, cfg.webhook.id, cfg.webhook.timeout)
        return _webhook
    return None


def notify_ha(event: str, **kwargs) -> bool:
    """Send a webhook event to Home Assistant (if configured)."""
    wh = _get_webhook()
    if not wh:
        return False
    try:
        payload: Dict[str, Any] = {
            "event": event,
            "device": cfg.app_name,
            "timestamp": getTimestamp(),
        }
        payload.update(kwargs)
        ok = wh.send(payload)
        if ok:
            log.debug("Webhook sent: %s", event)
        return ok
    except Exception as e:
        log.debug("Webhook error: %s", e)
        return False

# -*- coding: utf-8 -*-
"""Heartbeat – periodischer MQTT Status-Publish."""

import json
import threading
import time
from datetime import datetime
from typing import Optional


def _iso_now() -> str:
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S")


class Heartbeat:
    def __init__(self, mqtt_client, topic: str, logger, shutdown_mgr, interval_s: int = 60):
        self.mqtt_client = mqtt_client
        self.topic = topic
        self.logger = logger
        self.shutdown_mgr = shutdown_mgr
        self.interval_s = int(interval_s)
        self._thread: Optional[threading.Thread] = None
        self._start_ts: Optional[float] = None
        self._counter_lock = threading.Lock()
        self._readings_count = 0
        self._stop_flag = threading.Event()

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._start_ts = time.time()
        self._thread = threading.Thread(target=self._worker, name="heartbeat", daemon=True)
        self._thread.start()

    def increment(self, n: int = 1) -> None:
        with self._counter_lock:
            self._readings_count += int(n)

    def _payload(self, status: str) -> dict:
        with self._counter_lock:
            rc = self._readings_count
        since = datetime.fromtimestamp(self._start_ts or time.time()).strftime("%Y-%m-%dT%H:%M:%S")
        return {
            "status": status,
            "since": since,
            "uptime_s": int(time.time() - (self._start_ts or time.time())),
            "readings_count": rc,
            "interval_s": self.interval_s,
            "ts": _iso_now(),
        }

    def _worker(self) -> None:
        self.logger.info("Heartbeat gestartet, interval=%ds", self.interval_s)
        try:
            while not self.shutdown_mgr.is_set() and not self._stop_flag.is_set():
                try:
                    payload = json.dumps(self._payload("running"))
                    self.mqtt_client.publish(self.topic, payload, retain=True)
                except ConnectionRefusedError:
                    break
                except Exception:
                    self.logger.warning("Heartbeat publish failed", exc_info=True)

                if self.shutdown_mgr.wait(timeout=self.interval_s) or self._stop_flag.is_set():
                    break
        finally:
            try:
                payload = json.dumps(self._payload("offline"))
                self.mqtt_client.publish(self.topic, payload, retain=True)
            except Exception:
                pass

    def stop(self, join_timeout: float = 2.0) -> None:
        self._stop_flag.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=join_timeout)

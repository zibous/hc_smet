# -*- coding: utf-8 -*-
"""ShutdownManager – koordiniert sauberen Shutdown."""

import threading
from typing import Callable, List, Optional


class ShutdownManager:
    def __init__(self, logger):
        self.logger = logger
        self._event = threading.Event()
        self._completed = False
        self._lock = threading.Lock()
        self._callbacks: List[Callable[[], None]] = []

    def register(self, callback: Callable[[], None]) -> None:
        if not callable(callback):
            raise TypeError("callback must be callable")
        self._callbacks.append(callback)

    def initiate(self, per_callback_timeout: float = 5.0) -> None:
        with self._lock:
            if self._completed:
                return
            self._completed = True
            self._event.set()

        self.logger.info("ShutdownManager: initiating graceful shutdown")

        threads: list[tuple[threading.Thread, Callable[[], None]]] = []
        for cb in self._callbacks:
            t = threading.Thread(target=self._safe_call, args=(cb,), daemon=True)
            t.start()
            threads.append((t, cb))

        for t, cb in threads:
            t.join(per_callback_timeout)
            if t.is_alive():
                self.logger.warning("Shutdown callback %s did not finish in time", getattr(cb, "__name__", repr(cb)))

    def _safe_call(self, cb: Callable[[], None]) -> None:
        name = getattr(cb, "__name__", repr(cb))
        try:
            cb()
        except Exception:
            self.logger.exception("Shutdown callback failed: %s", name)

    def is_set(self) -> bool:
        return self._event.is_set()

    def wait(self, timeout: Optional[float] = None) -> bool:
        return self._event.wait(timeout)

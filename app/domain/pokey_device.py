# -*- coding: utf-8 -*-
"""PoKeysDevice — Repräsentation eines physischen PoKeys57E-Interfaces."""

import time


class PoKeysDevice:
    """Repräsentiert ein physisches PoKeys-Interface mit Online/Offline-Tracking."""

    def __init__(self, dev_id: str, ip: str, start_id: int, end_id: int):
        self.id = dev_id
        self.ip = ip
        self.start_id = start_id
        self.end_id = end_id
        self.online = False
        self.last_online_ts = 0
        self.sensors: list[str] = []

    def mark_online(self):
        self.online = True
        self.last_online_ts = time.time()

    def mark_offline(self):
        self.online = False

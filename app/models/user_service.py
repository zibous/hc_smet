# -*- coding: utf-8 -*-
"""Lädt User-Profile aus persons.yaml."""

import logging

import yaml

from app.models.person import UserProfile

log = logging.getLogger(__name__)


class UserService:
    def __init__(self, config_path: str = "config/persons.yaml"):
        with open(config_path, "r") as f:
            data = yaml.safe_load(f)

        self.users: list[UserProfile] = []
        for u in data.get("users", []):
            if not isinstance(u, dict):
                continue
            self.users.append(UserProfile(**u))

        log.info("Loaded %d user profiles", len(self.users))

    def all_users(self) -> list[UserProfile]:
        return self.users

    def find_by_name(self, name: str) -> UserProfile | None:
        name = name.strip().lower()
        return next((u for u in self.users if u.name.lower() == name), None)

    def find_best_by_weight(self, weight: float) -> UserProfile | None:
        best = None
        best_score = float("inf")
        for u in self.users:
            if u.is_plausible(weight):
                score = u.match_score(weight)
                if score < best_score:
                    best = u
                    best_score = score
        return best

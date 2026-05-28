# -*- coding: utf-8 -*-
from dataclasses import dataclass
from datetime import date
from typing import Any, Dict, Optional


@dataclass
class UserProfile:
    name: str
    sex: str
    height: int
    dob: str
    athletic: bool
    activity: float
    weight_threshold: float
    scores: Dict[str, float]
    adjustments: Optional[Dict[str, Any]] = None

    def age(self) -> float:
        """Alter in Jahren als Dezimalzahl."""
        birth = date.fromisoformat(self.dob)
        today = date.today()
        delta = today - birth
        return round(delta.days / 365.0, 2)

    def is_plausible(self, weight: float, tolerance: float = 10.0) -> bool:
        return abs(weight - self.scores["WEIGHT"]) <= tolerance

    def match_score(self, weight: float) -> float:
        return abs(weight - self.scores["WEIGHT"])

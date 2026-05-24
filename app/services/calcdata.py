# -*- coding: utf-8 -*-
"""Body Metrics Berechnung für MiScale."""

import json
import logging
import os
from datetime import datetime

from app.core.config import cfg
from app.models.person import UserProfile
from app.services import body_metrics, body_score

log = logging.getLogger(__name__)


def _local_now() -> str:
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S")


class CalcData:
    """Berechnet Body Metrics für einen User anhand von Waage-Rohdaten."""

    version = "2.0.0"

    def __init__(self, user: UserProfile, weight: float, impedance: int, timestamp: str | None = None):
        self.user = user
        self.weight = float(weight)
        self.impedance = int(impedance)
        self.timestamp = timestamp or _local_now()
        self.unit = "kg"
        self.data: dict = {}
        self.bodyscores: dict = {}

    def calculate(self) -> dict:
        """Führt die komplette Body-Metrics-Berechnung durch."""
        age = self.user.age()
        lib = body_metrics.bodyMetrics(self.weight, self.user.height, age, self.impedance, self.user.sex)

        d = self.data
        d["measured"] = round(self.weight, 2)
        d["weight"] = round(self.weight, 2)
        d["impedance"] = self.impedance
        d["unit"] = self.unit
        d["user"] = self.user.name
        d["sex"] = self.user.sex
        d["athletic"] = self.user.athletic
        d["age"] = round(age, 2)
        d["metabolic_age"] = round(lib.getMetabolicAge(), 2)
        d["bmi"] = round(lib.getBMI(), 2)
        d["poi"] = self._ponderal_index()
        d["bodytype"] = cfg.body_scale_types[lib.getBodyType()]
        d["idealweight"] = round(lib.getIdealWeight(), 2)
        d["targetweight"] = self.user.scores["WEIGHT"]
        d["lbm"] = round(lib.getLBMCoefficient(), 2)
        d["fat"] = round(lib.getFatPercentage(), 2)

        fat_ideal = lib.getFatMassToIdeal()
        d["fattype"] = fat_ideal["type"]
        d["idealfat"] = self.user.scores.get("FAT", round(fat_ideal["mass"], 2))

        d["visceral"] = round(lib.getVisceralFat(), 2)
        d["water"] = round(lib.getWaterPercentage(), 2)
        d["bone"] = round(lib.getBoneMass(), 2)
        d["muscle"] = round(lib.getMuscleMass(), 2)
        d["ffm"] = self._fatfreemass()
        d["ffmi"] = self._fatfreemass_index()
        d["protein"] = round(lib.getProteinPercentage(), 2)
        d["bmr"] = round(lib.getBMR(), 0)
        d["tdee"] = int(round(d["bmr"] * self.user.activity, 0))
        d["timestamp"] = self.timestamp

        self._apply_adjustments()
        return d

    def calculate_scores(self) -> dict:
        """Berechnet Body Scores und Deltas zum Vortag."""
        if not self.data:
            self.calculate()

        d = self.data
        scores = self.user.scores

        sc = body_score.bodyScore(
            self.user.age(),
            self.user.sex,
            self.user.height,
            self.weight,
            d["bmi"],
            float(scores["FAT"]),
            float(scores["MUSCLE"]),
            float(scores["WATER"]),
            float(scores["VISCERAL"]),
            float(scores["BONES"]),
            int(scores["BMR"]),
            float(scores["PROTEIN"]),
        )

        result = {"user": self.user.name, "score": sc.getBodyScore()}

        prev = self._load_previous()
        if prev:
            result["deltas"] = {
                "weight": round(d["weight"] - prev.get("weight", d["weight"]), 2),
                "fat": round(d["fat"] - prev.get("fat", d["fat"]), 2),
                "water": round(d["water"] - prev.get("water", d["water"]), 2),
                "muscle": round(d["muscle"] - prev.get("muscle", d["muscle"]), 2),
                "visceral": round(d["visceral"] - prev.get("visceral", d["visceral"]), 2),
                "protein": round(d["protein"] - prev.get("protein", d["protein"]), 2),
            }
            result["states"] = {
                "weight": self._diff_text(d["weight"], prev.get("weight", d["weight"])),
                "fat": self._diff_text(d["fat"], prev.get("fat", d["fat"])),
                "water": self._diff_text(d["water"], prev.get("water", d["water"])),
                "muscle": self._diff_text(d["muscle"], prev.get("muscle", d["muscle"])),
                "protein": self._diff_text(d["protein"], prev.get("protein", d["protein"])),
            }
        else:
            result["deltas"] = {k: 0.0 for k in ("weight", "fat", "water", "muscle", "visceral", "protein")}
            result["states"] = {k: cfg.diff_text[1] for k in ("weight", "fat", "water", "muscle", "protein")}

        result["scores"] = {
            "bmi": sc.getBmiDeductScore(),
            "fat": sc.getBodyFatDeductScore(),
            "visceral": sc.getVisceralFatDeductScore(),
            "muscle": sc.getMuscleDeductScore(),
            "water": sc.getWaterDeductScore(),
            "bones": sc.getBoneDeductScore(),
            "bmr": sc.getBasalMetabolismDeductScore(),
            "protein": sc.getProteinDeductScore(),
        }

        result["caloric"] = self._caloric_range()
        result["engergieexp"] = d.get("tdee", 0)
        result["macronut"] = self._macronutrients()
        result["timestamp"] = self.timestamp

        self.bodyscores = result
        return result

    def save_reference(self):
        """Speichert aktuelle Daten als JSON-Referenz."""
        if not self.data:
            return
        path = os.path.join(cfg.data_dir, f"miscale-{self.user.name}.json")
        try:
            with open(path, "w") as f:
                json.dump(self.data, f, ensure_ascii=False)
        except Exception:
            log.exception("Fehler beim Speichern der Referenzdaten: %s", path)

    # ─── Private Methoden ────────────────────────────────

    def _apply_adjustments(self):
        if not self.user.athletic:
            return
        w = self.weight
        d = self.data
        factors = {
            "fat": 0.018411 * w + (-0.6888),
            "water": 0.000908 * w + 0.9799,
            "bone": -0.001150 * w + 1.3863,
            "muscle": -0.016164 * w + 2.1373,
        }
        for field, factor in factors.items():
            if field in d:
                d[field] = round(d[field] * factor, 2)

    def _ponderal_index(self) -> float:
        return round(self.weight / ((self.user.height / 100) ** 3), 2)

    def _fatfreemass(self) -> float:
        bf = float(self.data["fat"])
        ffm = (self.weight * (1 - (bf / 100))) + 6.10 * (1.8 - (self.user.height / 100))
        return round(ffm, 2)

    def _fatfreemass_index(self) -> float:
        return round(self._fatfreemass() / ((self.user.height / 100) ** 2), 2)

    def _caloric_range(self) -> dict:
        return {
            "caloricmin": int(self.weight * 30.80),
            "caloricmax": int(self.weight * 35.20),
            "deficitmin": int(self.weight * 24.60),
            "deficitmax": int(self.weight * 28.20),
        }

    def _macronutrients(self) -> dict | None:
        tdee = self.data.get("tdee")
        if not tdee:
            return None
        return {
            "protein": round(tdee * 0.35, 0),
            "carbohydrates": round(tdee * 0.50, 0),
            "fat": round(tdee * 0.15, 0),
        }

    def _load_previous(self) -> dict | None:
        path = os.path.join(cfg.data_dir, f"miscale-{self.user.name}.json")
        try:
            if os.path.isfile(path):
                with open(path, "r") as f:
                    return json.load(f)
        except Exception:
            log.exception("Fehler beim Laden der Referenzdaten")
        return None

    @staticmethod
    def _diff_text(current: float, previous: float) -> str:
        if current < previous:
            return cfg.diff_text[0]
        elif current > previous:
            return cfg.diff_text[2]
        return cfg.diff_text[1]

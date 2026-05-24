#!/usr/bin/env python3
# -*- coding: utf-8 -*-


class bodyScales:
    def __init__(self, age: float, height: float, sex: str, weight: float, scaleType: str = "xiaomi"):
        self.age = age
        self.height = height
        self.sex = sex
        self.weight = weight
        self.scaleType = scaleType if scaleType == "xiaomi" else "holtek"

    def getBMIScale(self) -> list[float]:
        if self.scaleType == "xiaomi":
            return [18.5, 25.0, 28.0, 32.0]
        return [18.5, 25.0, 30.0]

    def getFatPercentageScale(self) -> list[float]:
        if self.scaleType == "xiaomi":
            scales = [
                {"min": 0, "max": 12, "female": [12.0, 21.0, 30.0, 34.0], "male": [7.0, 16.0, 25.0, 30.0]},
                {"min": 12, "max": 14, "female": [15.0, 24.0, 33.0, 37.0], "male": [7.0, 16.0, 25.0, 30.0]},
                {"min": 14, "max": 16, "female": [18.0, 27.0, 36.0, 40.0], "male": [7.0, 16.0, 25.0, 30.0]},
                {"min": 16, "max": 18, "female": [20.0, 28.0, 37.0, 41.0], "male": [7.0, 16.0, 25.0, 30.0]},
                {"min": 18, "max": 40, "female": [21.0, 28.0, 35.0, 40.0], "male": [11.0, 17.0, 22.0, 27.0]},
                {"min": 40, "max": 60, "female": [22.0, 29.0, 36.0, 41.0], "male": [12.0, 18.0, 23.0, 28.0]},
                {"min": 60, "max": 100, "female": [23.0, 30.0, 37.0, 42.0], "male": [14.0, 20.0, 25.0, 30.0]},
            ]
        else:
            scales = [
                {"min": 0, "max": 21, "female": [18.0, 23.0, 30.0, 35.0], "male": [8.0, 14.0, 21.0, 25.0]},
                {"min": 21, "max": 26, "female": [19.0, 24.0, 30.0, 35.0], "male": [10.0, 15.0, 22.0, 26.0]},
                {"min": 26, "max": 31, "female": [20.0, 25.0, 31.0, 36.0], "male": [11.0, 16.0, 21.0, 27.0]},
                {"min": 31, "max": 36, "female": [21.0, 26.0, 33.0, 36.0], "male": [13.0, 17.0, 25.0, 28.0]},
                {"min": 36, "max": 41, "female": [22.0, 27.0, 34.0, 37.0], "male": [15.0, 20.0, 26.0, 29.0]},
                {"min": 41, "max": 46, "female": [23.0, 28.0, 35.0, 38.0], "male": [16.0, 22.0, 27.0, 30.0]},
                {"min": 46, "max": 51, "female": [24.0, 30.0, 36.0, 38.0], "male": [17.0, 23.0, 29.0, 31.0]},
                {"min": 51, "max": 56, "female": [26.0, 31.0, 36.0, 39.0], "male": [19.0, 25.0, 30.0, 33.0]},
                {"min": 56, "max": 100, "female": [27.0, 32.0, 37.0, 40.0], "male": [21.0, 26.0, 31.0, 34.0]},
            ]

        for scale in scales:
            if self.age >= scale["min"] and self.age < scale["max"]:
                return scale[self.sex]  # type: ignore[literal-required]
        # Fallback: letzter Eintrag
        return scales[-1][self.sex]  # type: ignore[literal-required]

    def getMuscleMassScale(self) -> list[float]:
        if self.scaleType == "xiaomi":
            scales = [
                {"min": {"male": 170, "female": 160}, "female": [36.5, 42.6], "male": [49.4, 59.5]},
                {"min": {"male": 160, "female": 150}, "female": [32.9, 37.6], "male": [44.0, 52.5]},
                {"min": {"male": 0, "female": 0}, "female": [29.1, 34.8], "male": [38.5, 46.6]},
            ]
        else:
            scales = [
                {"min": {"male": 170, "female": 170}, "female": [36.5, 42.5], "male": [49.5, 59.4]},
                {"min": {"male": 160, "female": 160}, "female": [32.9, 37.5], "male": [44.0, 52.4]},
                {"min": {"male": 0, "female": 0}, "female": [29.1, 34.7], "male": [38.5, 46.5]},
            ]

        for scale in scales:
            if self.height >= scale["min"][self.sex]:  # type: ignore[index]
                return scale[self.sex]  # type: ignore[literal-required]
        return scales[-1][self.sex]  # type: ignore[literal-required]

    def getWaterPercentageScale(self) -> list[float]:
        if self.scaleType == "xiaomi":
            if self.sex == "male":
                return [55.0, 65.1]
            return [45.0, 60.1]
        return [53.0, 67.0]

    def getVisceralFatScale(self) -> list[float]:
        return [10.0, 15.0]

    def getBoneMassScale(self) -> list[float]:
        if self.scaleType == "xiaomi":
            scales = [
                {"male": {"min": 75.0, "scale": [2.0, 4.2]}, "female": {"min": 60.0, "scale": [1.8, 3.9]}},
                {"male": {"min": 60.0, "scale": [1.9, 4.1]}, "female": {"min": 45.0, "scale": [1.5, 3.8]}},
                {"male": {"min": 0.0, "scale": [1.6, 3.9]}, "female": {"min": 0.0, "scale": [1.3, 3.6]}},
            ]
            for scale in scales:
                if self.weight >= scale[self.sex]["min"]:  # type: ignore[literal-required]
                    return scale[self.sex]["scale"]  # type: ignore[literal-required]
            return scales[-1][self.sex]["scale"]  # type: ignore[literal-required]
        else:
            scales_h = [
                {"female": {"min": 60.0, "optimal": 2.5}, "male": {"min": 75.0, "optimal": 3.2}},
                {"female": {"min": 45.0, "optimal": 2.2}, "male": {"min": 69.0, "optimal": 2.9}},
                {"female": {"min": 0.0, "optimal": 1.8}, "male": {"min": 0.0, "optimal": 2.5}},
            ]
            for scale in scales_h:
                if self.weight >= scale[self.sex]["min"]:  # type: ignore[literal-required]
                    opt = scale[self.sex]["optimal"]  # type: ignore[literal-required]
                    return [opt - 1, opt + 1]
            opt = scales_h[-1][self.sex]["optimal"]  # type: ignore[literal-required]
            return [opt - 1, opt + 1]

    def getBMRScale(self) -> list[float]:
        if self.scaleType == "xiaomi":
            coefficients: dict[int, float] = {30: 21.6, 50: 20.07, 100: 19.35}
        else:
            if self.sex == "female":
                coefficients = {12: 34, 15: 29, 17: 24, 29: 22, 50: 20, 120: 19}
            else:
                coefficients = {12: 36, 15: 30, 17: 26, 29: 23, 50: 21, 120: 20}

        for age, coefficient in coefficients.items():
            if self.age < age:
                return [self.weight * coefficient]
        # Fallback: letzter Koeffizient
        last = list(coefficients.values())[-1]
        return [self.weight * last]

    def getProteinPercentageScale(self) -> list[float]:
        return [16.0, 20.0]

    def getIdealWeightScale(self) -> list[float]:
        bmi_scale = self.getBMIScale()
        return [(b * self.height) * self.height / 10000 for b in bmi_scale]

    def getBodyScoreScale(self) -> list[float]:
        return [50.0, 60.0, 80.0, 90.0]

    def getBodyTypeScale(self) -> list[str]:
        return [
            "obese",
            "overweight",
            "thick-set",
            "lack-exerscise",
            "balanced",
            "balanced-muscular",
            "skinny",
            "balanced-skinny",
            "skinny-muscular",
        ]

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Testcase: Berechnung mit Vergleich zu data/miscale-Peter.json und data/miscale-Reni.json.

Aufruf: python3 -m testcase.test_calcdata  (aus home-miscale/)
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.calcdata import CalcData
from model.user_service import UserService


def load_reference(name: str) -> dict:
    path = os.path.join("data", f"miscale-{name}.json")
    with open(path, "r") as f:
        return json.load(f)


def compare(label: str, calculated: float, reference: float, tolerance: float = 1.0):
    diff = abs(calculated - reference)
    status = "✅" if diff <= tolerance else "❌"
    print(f"  {status} {label:20s}: berechnet={calculated:8.2f}  referenz={reference:8.2f}  diff={diff:.2f}")
    return diff <= tolerance


def test_user(user_service: UserService, name: str, weight: float, impedance: int, timestamp: str):
    print(f"\n{'=' * 60}")
    print(f"Test: {name} – weight={weight}, impedance={impedance}")
    print(f"{'=' * 60}")

    user = user_service.find_by_name(name)
    if not user:
        print(f"  ❌ User '{name}' nicht gefunden!")
        return False

    calc = CalcData(user, weight, impedance, timestamp)
    data = calc.calculate()
    scores = calc.calculate_scores()

    ref = load_reference(name)

    fields = [
        "bmi",
        "fat",
        "water",
        "bone",
        "muscle",
        "visceral",
        "protein",
        "lbm",
        "poi",
        "ffm",
        "ffmi",
    ]

    # Altersabhängige Felder mit größerer Toleranz (Alter ändert sich seit Referenz)
    age_fields = ["metabolic_age"]

    all_ok = True
    for field in fields:
        if field in ref and field in data:
            ok = compare(field, data[field], ref[field], tolerance=2.0)
            if not ok:
                all_ok = False

    for field in age_fields:
        if field in ref and field in data:
            ok = compare(field, data[field], ref[field], tolerance=5.0)
            if not ok:
                all_ok = False

    # BMR mit größerer Toleranz (altersabhängig)
    if "bmr" in ref:
        compare("bmr", data["bmr"], ref["bmr"], tolerance=50)

    # TDEE prüfen wir gegen BMR × activity (nicht gegen Referenz,
    # da die alte Version einen Bug hatte: Peters activity für alle User)
    expected_tdee = int(round(data["bmr"] * user.activity, 0))
    compare("tdee (berechnet)", data["tdee"], expected_tdee, tolerance=1)

    print(f"\n  Bodytype: {data['bodytype']}")
    print(f"  Score:    {scores.get('score', 'N/A')}")
    print(f"  TDEE:     {data.get('tdee', 'N/A')} kcal")

    return all_ok


def main():
    user_service = UserService()

    # Peter: weight=69.25, impedance=586
    ok_peter = test_user(
        user_service,
        "Peter",
        weight=69.25,
        impedance=586,
        timestamp="2026-04-23T17:55:00",
    )

    # Reni: weight=48.95, impedance=676
    ok_reni = test_user(
        user_service,
        "Reni",
        weight=48.95,
        impedance=676,
        timestamp="2026-04-23T17:55:00",
    )

    print(f"\n{'=' * 60}")
    if ok_peter and ok_reni:
        print("✅ Alle Tests bestanden")
    else:
        print("❌ Einige Tests fehlgeschlagen")
        sys.exit(1)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Vergleich: Adjustments vs. Interpolation vs. Athleten-Formel

Testet Peters Daten bei verschiedenen Gewichten und zeigt die Unterschiede
zwischen den drei Ansätzen für fat, water, bone, muscle.

Aufruf: python3 -m testcase.compare_athletic  (aus home-miscale/)
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib import body_metrics
from model.user_service import UserService


def get_raw_values(weight: float, height: int, age: float, impedance: int, sex: str) -> dict:
    """Rohwerte aus body_metrics (ohne jede Korrektur)."""
    lib = body_metrics.bodyMetrics(weight, height, age, impedance, sex)
    return {
        "fat": round(lib.getFatPercentage(), 2),
        "water": round(lib.getWaterPercentage(), 2),
        "bone": round(lib.getBoneMass(), 2),
        "muscle": round(lib.getMuscleMass(), 2),
    }


def apply_adjustments(raw: dict, adjustments: dict, weight: float) -> dict:
    """Variante 1: Exakter Key-Lookup (aktuelles Verfahren)."""
    idx = str(round(weight, 1))
    if idx not in adjustments:
        return {k: (v, "⚠ kein Key") for k, v in raw.items()}
    cf = adjustments[idx]
    return {
        "fat": round(raw["fat"] * cf.get("fat", 1.0), 2),
        "water": round(raw["water"] * cf.get("water", 1.0), 2),
        "bone": round(raw["bone"] * cf.get("bone", 1.0), 2),
        "muscle": round(raw["muscle"] * cf.get("muscle", 1.0), 2),
    }


def interpolate_adjustments(raw: dict, adjustments: dict, weight: float) -> dict:
    """Variante 2: Lineare Interpolation zwischen den zwei nächsten Keys."""
    keys = sorted([float(k) for k in adjustments.keys()])
    w = round(weight, 1)

    # Exakter Treffer?
    if str(w) in adjustments:
        cf = adjustments[str(w)]
        return {
            "fat": round(raw["fat"] * cf.get("fat", 1.0), 2),
            "water": round(raw["water"] * cf.get("water", 1.0), 2),
            "bone": round(raw["bone"] * cf.get("bone", 1.0), 2),
            "muscle": round(raw["muscle"] * cf.get("muscle", 1.0), 2),
        }

    # Nächste Nachbarn finden
    lower = [k for k in keys if k <= w]
    upper = [k for k in keys if k >= w]

    if not lower or not upper:
        return {k: (v, "⚠ außerhalb") for k, v in raw.items()}

    lo = lower[-1]
    hi = upper[0]

    if lo == hi:
        cf = adjustments[str(lo)]
        t = 0.0
    else:
        t = (w - lo) / (hi - lo)
        cf_lo = adjustments[str(lo)]
        cf_hi = adjustments[str(hi)]
        cf = {}
        for field in ("fat", "water", "bone", "muscle"):
            v_lo = cf_lo.get(field, 1.0)
            v_hi = cf_hi.get(field, 1.0)
            cf[field] = v_lo + t * (v_hi - v_lo)

    return {
        "fat": round(raw["fat"] * cf.get("fat", 1.0), 2),
        "water": round(raw["water"] * cf.get("water", 1.0), 2),
        "bone": round(raw["bone"] * cf.get("bone", 1.0), 2),
        "muscle": round(raw["muscle"] * cf.get("muscle", 1.0), 2),
    }


def athletic_formula(weight: float, height: int, age: float, impedance: int, sex: str) -> dict:
    """
    Variante 3: Athleten-Formel.

    Angepasste Berechnung für Athleten – niedrigerer Fettanteil,
    höherer Muskelanteil durch modifizierte Koeffizienten.
    Basiert auf Forschung zu BIA bei trainierten Personen.
    """
    lib = body_metrics.bodyMetrics(weight, height, age, impedance, sex)
    lbm = lib.getLBMCoefficient()

    # Athleten haben typisch 2-5% weniger Fett als Standard-BIA zeigt
    # Korrektur: LBM-Konstante anpassen (athletischer Körper = mehr Lean Mass)
    if sex == "male":
        const = -1.2  # statt 0.8 → mehr LBM → weniger Fett
    else:
        const = 3.0

    if sex == "male" and weight < 61:
        coefficient = 0.98
    elif sex == "female" and weight > 60:
        coefficient = 0.96
        if height > 160:
            coefficient *= 1.03
    elif sex == "female" and weight < 50:
        coefficient = 1.02
        if height > 160:
            coefficient *= 1.03
    else:
        coefficient = 1.0

    fat = (1.0 - (((lbm - const) * coefficient) / weight)) * 100
    fat = max(3.0, min(fat, 75.0))

    water = (100 - fat) * 0.7
    if water <= 50:
        water *= 1.02
    else:
        water *= 0.98
    water = max(35.0, min(water, 75.0))

    bone = lib.getBoneMass()

    muscle = weight - (fat * 0.01 * weight) - bone
    muscle = max(10.0, min(muscle, 120.0))

    return {
        "fat": round(fat, 2),
        "water": round(water, 2),
        "bone": round(bone, 2),
        "muscle": round(muscle, 2),
    }


def main():
    user_service = UserService()
    peter = user_service.find_by_name("Peter")
    if not peter:
        print("Peter nicht gefunden!")
        sys.exit(1)

    age = peter.age()
    adj = peter.adjustments or {}

    # Testgewichte: einige mit exaktem Key, einige ohne
    test_cases = [
        (67.15, 574),  # aus Referenzdaten
        (69.25, 586),  # aus Referenzdaten
        (69.15, 586),  # KEIN exakter Key → Adjustment greift nicht
        (70.0, 557),
        (70.35, 557),  # KEIN exakter Key
        (71.5, 535),
        (73.75, 593),  # aus ESP-Testdaten
    ]

    print(f"{'=' * 100}")
    print(f"Vergleich Athletic-Modus: Peter (age={age:.1f}, height={peter.height})")
    print(f"{'=' * 100}")
    print()

    header = f"{'Gewicht':>8} {'Imp':>4} │ {'Feld':>7} │ {'Roh':>8} │ {'Adj(exakt)':>10} │ {'Adj(interp)':>11} │ {'Athleten':>10}"
    sep = "─" * len(header)

    for weight, impedance in test_cases:
        raw = get_raw_values(weight, peter.height, age, impedance, peter.sex)
        adj_exact = apply_adjustments(raw, adj, weight)
        adj_interp = interpolate_adjustments(raw, adj, weight)
        ath = athletic_formula(weight, peter.height, age, impedance, peter.sex)

        has_key = str(round(weight, 1)) in adj
        key_info = "✅" if has_key else "⚠ kein Key"

        print(sep)
        print(f"{weight:>7.2f}kg {impedance:>4}Ω  [{key_info}]")
        print(sep)

        for field in ("fat", "water", "bone", "muscle"):
            r = raw[field]
            # adj_exact kann tuple sein wenn kein Key
            ae = adj_exact[field]
            if isinstance(ae, tuple):
                ae_str = f"{ae[0]:>8.2f} ⚠"
            else:
                ae_str = f"{ae:>10.2f}"

            ai = adj_interp[field]
            if isinstance(ai, tuple):
                ai_str = f"{ai[0]:>8.2f} ⚠"
            else:
                ai_str = f"{ai:>11.2f}"

            a = ath[field]
            print(f"{'':>14} │ {field:>7} │ {r:>8.2f} │ {ae_str} │ {ai_str} │ {a:>10.2f}")

        print()

    print(f"{'=' * 100}")
    print("Legende:")
    print("  Roh         = body_metrics ohne Korrektur")
    print("  Adj(exakt)  = Korrekturfaktor per exaktem Gewichts-Key (aktuell)")
    print("  Adj(interp) = Korrekturfaktor mit linearer Interpolation")
    print("  Athleten    = Modifizierte Formel für Athleten (ohne Adjustments)")
    print("  ⚠           = Kein passender Key → Rohwert unverändert")


if __name__ == "__main__":
    main()

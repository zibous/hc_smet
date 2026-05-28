#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Simuliert ESP32-Messungen – Berechnung + optional MQTT publish.

Aufruf:
  python3 -m testcase.simulate                    (nur Konsole)
  python3 -m testcase.simulate --mqtt             (+ publish nach bodyscale/test/...)
  python3 -m testcase.simulate --mqtt --user Reni (nur Reni)
"""

import argparse
import json
import logging
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(name)s - %(message)s", stream=sys.stdout
)

from lib.calcdata import CalcData
from model.user_service import UserService


def simulate(user_service: UserService, name: str, weight: float, impedance: int, timestamp: str, mqtt_client=None):
    print(f"\n{'─' * 60}")
    print(f"Simulate: {name} – weight={weight} kg, impedance={impedance} Ω")
    print(f"{'─' * 60}")

    user = user_service.find_by_name(name)
    if not user:
        print(f"  ❌ User '{name}' nicht gefunden!")
        return

    calc = CalcData(user, weight, impedance, timestamp)
    data = calc.calculate()
    scores = calc.calculate_scores()

    print("\n  Body Data:")
    print(json.dumps(data, indent=4, ensure_ascii=False))

    print("\n  Scores:")
    print(json.dumps(scores, indent=4, ensure_ascii=False))

    if mqtt_client and mqtt_client.ready:
        topic_data = f"bodyscale/test/{name}/data"
        topic_scores = f"bodyscale/test/{name}/scores"
        mqtt_client.publish(topic_data, data, retain=False)
        mqtt_client.publish(topic_scores, scores, retain=False)
        print(f"\n  ✅ MQTT → {topic_data}")
        print(f"  ✅ MQTT → {topic_scores}")


def main():
    parser = argparse.ArgumentParser(description="MiScale Simulation")
    parser.add_argument("--mqtt", action="store_true", help="Publish nach bodyscale/test/...")
    parser.add_argument("--user", default=None, help="Nur diesen User simulieren")
    args = parser.parse_args()

    user_service = UserService()
    mqtt_client = None

    if args.mqtt:
        from lib.mqtt import MqttClient

        mqtt_client = MqttClient()
        if mqtt_client.ready:
            print("MQTT verbunden → publish nach bodyscale/test/...")
        else:
            print("⚠ MQTT nicht erreichbar – nur Konsole")
            mqtt_client = None

    tests = [
        ("Peter", 69.25, 586, "2026-04-23T17:55:00"),
        ("Reni", 48.95, 676, "2026-04-23T17:55:00"),
    ]

    for name, weight, impedance, ts in tests:
        if args.user and args.user.lower() != name.lower():
            continue
        simulate(user_service, name, weight, impedance, ts, mqtt_client)


if __name__ == "__main__":
    main()

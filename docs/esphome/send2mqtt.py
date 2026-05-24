#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test-Script: Simuliert einen ESP32 HTTP POST an die Flask App.

Dieses Script ist ein Hilfsmittel zum Testen – der echte ESP32
sendet die Daten direkt per HTTP POST (siehe mismartscale-http.yaml).

Aufruf: python3 esphome/send2mqtt.py
"""

import json
from datetime import datetime

import requests

URL = "http://10.1.1.119:5000/miscale"


def send_measurement(user_id: int, name: str, weight: float, impedance: int) -> None:
    data = {
        "id": user_id,
        "name": name,
        "weight": round(weight, 2),
        "impedance": impedance,
        "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
    }
    try:
        print(f"Sending: {json.dumps(data)}")
        response = requests.post(URL, json=data, timeout=5)
        print(f"Response: {response.status_code} → {response.json()}")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    # Peter
    send_measurement(1, "Peter", 69.25, 586)
    print()
    # Reni
    send_measurement(2, "Reni", 48.95, 676)

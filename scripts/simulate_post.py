#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simuliert einen ESP32 POST an /miscale.

Usage:
    python scripts/simulate_post.py                  # Default: Peter, 69.5kg
    python scripts/simulate_post.py --user Reni --weight 53.2 --impedance 520
    python scripts/simulate_post.py --remove         # Letzten Eintrag aus DB entfernen
"""

import argparse
import json
from datetime import datetime

import requests


def simulate_post(host: str, port: int, user: str, weight: float, impedance: int):
    """Sendet einen simulierten POST an /miscale."""
    url = f"http://{host}:{port}/miscale"
    payload = {
        "name": user,
        "weight": weight,
        "impedance": impedance,
        "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
    }

    print(f"POST → {url}")
    print(f"  Payload: {json.dumps(payload, indent=2)}")

    try:
        resp = requests.post(url, json=payload, timeout=10)
        print(f"  Status: {resp.status_code}")
        print(f"  Response: {resp.json()}")
        return resp.status_code == 200
    except Exception as e:
        print(f"  Fehler: {e}")
        return False


def remove_last(db_path: str, user: str):
    """Entfernt den letzten Eintrag eines Users aus der DB."""
    import sqlite3

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    # Letzten Eintrag finden
    row = conn.execute(
        "SELECT date, weight FROM daily_miscale WHERE LOWER(name)=? ORDER BY date DESC LIMIT 1",
        (user.lower(),),
    ).fetchone()

    if not row:
        print(f"Kein Eintrag für {user} gefunden")
        conn.close()
        return False

    print(f"Lösche: {user} | {row['date']} | {row['weight']} kg")
    conn.execute(
        "DELETE FROM daily_miscale WHERE LOWER(name)=? AND date=?",
        (user.lower(), row["date"]),
    )
    conn.commit()
    conn.close()
    print("✅ Gelöscht")
    return True


def main():
    parser = argparse.ArgumentParser(description="MiScale POST Simulator")
    parser.add_argument("--host", default="10.1.1.119", help="Server Host")
    parser.add_argument("--port", type=int, default=5056, help="Server Port")
    parser.add_argument("--user", default="Peter", help="User Name")
    parser.add_argument("--weight", type=float, default=69.5, help="Gewicht in kg")
    parser.add_argument("--impedance", type=int, default=580, help="Impedanz")
    parser.add_argument("--remove", action="store_true", help="Letzten Eintrag entfernen")
    parser.add_argument("--db", default="data/miscaledata.db", help="DB Pfad")

    args = parser.parse_args()

    if args.remove:
        remove_last(args.db, args.user)
    else:
        simulate_post(args.host, args.port, args.user, args.weight, args.impedance)


if __name__ == "__main__":
    main()

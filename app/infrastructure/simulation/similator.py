import numpy as np
import pandas as pd
from datetime import datetime
import hashlib

# -----------------------------
# Strukturierte Daten aus YAML laden
# -----------------------------
import app.domain.house as house
STRUCTURE = house.load_house_yaml()

# -----------------------------
# STRUCTURE HELPERS (AREAS, ROOMS, SENSORS)
# -----------------------------
def get_areas():
    return STRUCTURE["areas"]

def get_rooms():
    return STRUCTURE["rooms"]

def get_sensors():
    return STRUCTURE["sensors"]

# -----------------------------
# HIERARCHIE: HOME -> AREAS -> ROOMS -> SENSORS
# -----------------------------
def get_children(node):
    result = []
    # HOME -> AREAS
    if node == "HOME":
        for area_id, area in STRUCTURE["areas"].items():
            result.append({
                "id": area_id,
                "name": area["name"],
                "type": "area"
            })
        return result
    # AREA -> ROOMS
    if node in STRUCTURE["areas"]:
        for room_id, room in STRUCTURE["rooms"].items():
            if room["area"] == node:
                result.append({
                    "id": room_id,
                    "name": room["name"],
                    "type": "room"
                })
        return result
    # ROOM -> SENSORS
    if node in STRUCTURE["rooms"]:
        for sensor_id, sensor in STRUCTURE["sensors"].items():
            if sensor["room"] == node:
                result.append({
                    "id": sensor_id,
                    "name": sensor["name"],
                    "type": "sensor",
                    "devices": sensor["devices"]
                })
        return result
    return result


def shift_range(start, end):
    duration = end - start
    return start - duration, start

# -----------------------------
# STABLE SEED
# -----------------------------
def stable_seed(period_name: str, start: datetime, end: datetime):
    key = f"{period_name}:{start.date()}:{end.date()}"
    return int(hashlib.md5(key.encode()).hexdigest()[:8], 16)

# -----------------------------------------------------------------------
# SIMULATION (EINFACH & NODE-AWARE)
# -----------------------------------------------------------------------
def generate(start, end, freq, period_name: str = "", node: str = "HOME"):
    times = pd.date_range(start, end, freq=freq)
    np.random.seed(stable_seed(period_name, start, end))

    # Node → Keys
    if node == "HOME":
        keys = list(get_areas().keys())
    elif node in get_areas():
        keys = [r_id for r_id, r in get_rooms().items() if r["area"] == node]
    elif node in get_rooms():
        keys = [s_id for s_id, s in get_sensors().items() if s["room"] == node]
    elif node in get_sensors():
        keys = [node]
    else:
        keys = []

    # SERIES GENERATION
    series = {}
    for k in keys:
        values = []
        for t in times:
            hour = t.hour
            if 6 <= hour <= 9:
                profile = 2.5
            elif 17 <= hour <= 22:
                profile = 3.5
            elif 0 <= hour <= 5:
                profile = 0.8
            else:
                profile = 1.5

            base = np.random.uniform(0.5, 2.0)
            noise = np.random.normal(0, 0.2)
            values.append(max(0, base + profile + noise))

        series[k] = values

    # LABELS
    labels = {}
    if node == "HOME":
        level = 1
        for k, v in get_areas().items():
            labels[k] = v["name"]
    elif node in get_areas():
        level = 2
        for k, v in get_rooms().items():
            if v["area"] == node:
                labels[k] = v["name"]
    elif node in get_rooms():
        level = 3
        for k, v in get_sensors().items():
            if v["room"] == node:
                labels[k] = v["name"]
    else:
        level = 4
        for k in keys:
            labels[k] = k

    # STATS
    stats = {}
    for k, values in series.items():
        arr = np.array(values, dtype=float)
        if len(arr):
            current = float(arr[-1])
            prev = float(arr[-2]) if len(arr) > 1 else current
            delta = ((current - prev) / prev * 100) if prev != 0 else 0
            stats[k] = {
                "min": float(arr.min()),
                "max": float(arr.max()),
                "avg": float(arr.mean()),
                "current": current,
                "delta": delta
            }
        else:
            stats[k] = {"min": 0, "max": 0, "avg": 0, "current": 0, "delta": 0}

    return {
        "time": [t.strftime("%Y-%m-%d %H:%M") for t in times],
        "series": series,
        "labels": labels,
        "level": level,
        "stats": stats
    }


def build_kpis(current, previous=None, period="today"):
    if not current:
        current = {}
    series = current.get("series", {})

    all_values = np.concatenate(
        [np.array(v, dtype=float) for v in series.values()]
    ) if series else np.array([0.0])

    total = float(all_values.sum())
    avg = float(all_values.mean())
    peak = float(all_values.max())

    delta = 0.0

    if previous:
        prev_series = previous.get("series", {})
        prev_values = np.concatenate(
            [np.array(v, dtype=float) for v in prev_series.values()]
        ) if prev_series else np.array([0.0])

        prev_total = float(prev_values.sum())
        if prev_total != 0:
            delta = (total - prev_total) / prev_total * 100

    cost = total * 0.35

    return {
        "total": round(total, 1),
        "avg": round(avg, 2),
        "peak": round(peak, 1),
        "cost": round(cost, 2),
        "delta": round(delta, 1)
    }

def build_cards(node, current, period="today", previous=None):
    children = get_children(node)

    if not current:
        current = {}
    series = current.get("series", {})
    labels = current.get("labels", {})

    prev_series = previous.get("series", {}) if previous else {}

    items = []

    for c in children:
        key = c["id"]
        if key not in series:
            continue

        values = np.array(series[key], dtype=float)

        value = float(values.sum())
        min_v = float(values.min())
        max_v = float(values.max())
        avg_v = float(values.mean())

        # ECHTE DELTA-BERECHNUNG: Wenn Simulations-Vergleichsdaten vorhanden sind
        if key in prev_series and len(prev_series[key]) > 0:
            prev_values = np.array(prev_series[key], dtype=float)
            prev_total = float(prev_values.sum())
            delta = ((value - prev_total) / prev_total * 100) if prev_total != 0 else 0
        else:
            prev = values[-2] if len(values) > 1 else values[-1]
            delta = ((values[-1] - prev) / prev * 100) if prev != 0 else 0

        items.append({
            "id": key,
            "name": labels.get(key, key),
            "type": c["type"],
            "devices": c.get("devices", []),
            "value": round(value, 1),
            "delta": round(delta, 1),
            "min": round(min_v, 1),
            "max": round(max_v, 1),
            "avg": round(avg_v, 1)
        })

    return {
        "node": node,
        "items": items
    }


def build_timeseries(current, previous, period, node):
    return {
        "current": current,
        "previous": previous,
        "period": period,
        "node": node
    }

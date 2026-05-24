from datetime import datetime
import hashlib
import numpy as np

import app.domain.house as house
from app.core.app_config import settings

import logging
logger = logging.getLogger(__name__)

# -----------------------------
# Strukturierte Daten aus YAML laden (Liefert ein stabile Dictionary)
# -----------------------------
STRUCTURE = house.load_house_yaml()

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


def build_kpis(current, previous=None, period="today"):
    if not current:
        current = {}
    series = current.get("series", {})

    logger.debug(f"KPI build für periode: {period}")

    arrays = [np.asarray(v, dtype=float) for v in series.values() if len(v) > 0]

    if len(arrays) == 0:
        all_values = np.array([], dtype=float)
    else:
        all_values = np.concatenate(arrays)

    if all_values.size == 0:
        return {
            "total": 0.0,
            "avg": 0.0,
            "peak": 0.0,
            "cost": 0.0,
            "delta": 0.0
        }

    total = float(all_values.sum())
    avg = float(all_values.mean())
    peak = float(all_values.max())

    delta = 0.0

    if previous:
        prev_series = previous.get("series", {})
        prev_arrays = [np.asarray(v, dtype=float) for v in prev_series.values() if len(v) > 0]

        if len(prev_arrays) > 0:
            prev_values = np.concatenate(prev_arrays)
            prev_total = float(prev_values.sum())

            if prev_total != 0:
                delta = (total - prev_total) / prev_total * 100

    ## -----------------------------------------------------------------------
    ## TODO: how to get the YEAR ??
    ## 1. get from settings.STROMPREISE = json.loads(os.getenv("STROMPREISE"))
    ## 2. preis = STROMPREISE.get("2026", 0.24)
    ## -----------------------------------------------------------------------
    _kwhpreis = 0.24
    cost = total * _kwhpreis

    return {
        "total": round(total, 1),
        "avg": round(avg, 2),
        "peak": round(peak, 1),
        "cost": round(cost, 2),
        "delta": round(delta, 1)
    }


def build_cards(node, current, period="today", previous=None):
    logger.debug(f"Cards build für periode: {period}, Node: {node}")

    if not current:
        current = {}
    series = current.get("series", {})
    labels = current.get("labels", {})
    stats = current.get("stats", {})

    # 🔧 HIER DIE RETTUNG: Wir holen das numerische Level direkt aus den Repository-Daten
    current_level = current.get("level", 1)
    prev_series = previous.get("series", {}) if previous else {}

    items = []


    # =================================================================
    # 💡 MULTI-CARD ANALYTICS STECKBRIEF (Wenn das aktuelle Level 4 ist)
    # =================================================================
    current_level = current.get("level", 1) if current else 1

    if current_level == 4:
        # Laden der Analytics-Metriken aus dem neuen, separaten Repository
        from app.infrastructure.database.analytics_repository import load_sensor_analytics
        analytics = load_sensor_analytics(node)

        if node in series and len(series[node]) > 0:
            values = np.array(series[node], dtype=float)
            value = float(values.sum())
            min_v = float(values.min())
            max_v = float(values.max())
            avg_v = float(values.mean())

            if node in prev_series and len(prev_series[node]) > 0:
                prev_values = np.array(prev_series[node], dtype=float)
                prev_total = float(prev_values.sum())
                delta = ((value - prev_total) / prev_total * 100) if prev_total != 0 else 0
            else:
                prev = values[-2] if len(values) > 1 else values[-1]
                delta = ((values[-1] - prev) / prev * 100) if prev != 0 else 0

            sensor_name = labels.get(node, node)

            # Wenn Analytics-Einträge existieren, fächern wir die Informationen auf!
            if analytics:
                items.extend([
                    {
                        "id": node, "name": f"📊 Profil: {sensor_name} (Cluster {analytics['cluster']})",
                        "type": "sensor", "level": 4, "devices": STRUCTURE["sensors"].get(node, {}).get("devices", []),
                        "value": round(value, 1), "delta": round(delta, 1),
                        "min": round(min_v, 1), "max": round(max_v, 1), "avg": round(avg_v, 1)
                    },
                    {
                        "id": f"{node}_load", "name": "📉 Auslastungsfaktor (Load Factor)",
                        "type": "sensor", "level": 4, "devices": [],
                        "value": round(analytics["load_factor"] * 100, 1), "delta": 0,
                        "min": round(analytics["minimum"], 2), "max": round(analytics["maximum"], 2), "avg": round(analytics["median"], 2)
                    },
                    {
                        "id": f"{node}_base", "name": "💤 Grundlast (Standby / Base-Zone)",
                        "type": "sensor", "level": 4, "devices": [],
                        "value": round(analytics["base"], 1), "delta": 0,
                        "min": 0, "max": 0, "avg": 0
                    },
                    {
                        "id": f"{node}_peak", "name": "🔥 Spitzenlast (Peak-Zone)",
                        "type": "sensor", "level": 4, "devices": [],
                        "value": round(analytics["peak"], 1), "delta": round(analytics["peak_percent"], 1),
                        "min": 0, "max": 0, "avg": 0
                    }
                ])
            else:
                # Fallback: Wenn für das Gerät kein Analytics-Profil berechnet wurde
                items.append({
                    "id": node, "name": sensor_name,
                    "type": "sensor", "level": 4, "devices": STRUCTURE["sensors"].get(node, {}).get("devices", []),
                    "value": round(value, 1), "delta": round(delta, 1),
                    "min": round(min_v, 1), "max": round(max_v, 1), "avg": round(avg_v, 1)
                })

        return {
            "node": node,
            "items": items
        }


    # =================================================================
    # REGULÄRE LOGIK (Für HOME, AREAS, ROOMS - Level 1, 2 und 3)
    # =================================================================
    children = get_children(node)

    for c in children:
        key = c["id"]
        if key not in series:
            continue

        values = np.array(series[key], dtype=float)

        if len(values) == 0:
            items.append({
                "id": key,
                "name": labels.get(key, key),
                "type": c["type"],
                "devices": c.get("devices", []),
                "value": 0,
                "delta": 0,
                "min": 0,
                "max": 0,
                "avg": 0
            })
            continue

        value = float(values.sum())
        min_v = float(values.min())
        max_v = float(values.max())
        avg_v = float(values.mean())

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
            "level": current_level,
            "devices": c.get("devices", []),
            "value": round(value, 1),
            "delta": round(delta, 1),
            "min": round(min_v, 1),
            "max": round(max_v, 1),
            "avg": round(avg_v, 1)
        })

    return {
        "node": node,
        "level": current_level, # Reicht die 1, 2 oder 3 an cards.js weiter
        "items": items,
        "stats": stats
    }


def build_timeseries(current, previous, period, node):
    logger.debug(f"Timeseries build für periode: {period},  Node: {node}")
    return {
        "current": current,
        "previous": previous,
        "period": period,
        "node": node
    }

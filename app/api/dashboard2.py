import logging
import time
from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.core.app_config import settings
from app.infrastructure.database.dbconnect import Database
from app.infrastructure.database.analytics_repository import load_sensor_analytics
import app.domain.house as house

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/dashboard2", tags=["dashboard2"])

# Haus-Topologie
STRUCTURE = house.STRUCTURE


# =================================================================
# API: Live-Sensorwerte aus dem RAM
# =================================================================
@router.get("/live/sensors")
async def get_live_sensors():
    """Liefert die aktuellen Sensorwerte aus dem RAM-Speicher (sensor_state.json)."""
    from app.api.parsdecoder import _shared_store

    store_data = _shared_store.get_all()
    sensors_info = STRUCTURE.get("sensors", {})
    rooms_info = STRUCTURE.get("rooms", {})
    areas_info = STRUCTURE.get("areas", {})

    result = []
    for sensor_id in sorted(store_data.keys()):
        entry = store_data[sensor_id]
        meta = sensors_info.get(sensor_id, {})
        room_id = meta.get("room", "")
        room_data = rooms_info.get(room_id, {})
        room_name = room_data.get("name", "-")
        area_id = room_data.get("area", "")
        area_name = areas_info.get(area_id, {}).get("name", "-")

        # nur aktive Sensoren anzeigen
        if entry.current <= 0:
            continue

        result.append({
            "id": sensor_id,
            "name": meta.get("name", sensor_id),
            "room": room_name,
            "area": area_name,
            "area_id": area_id,
            "current": round(entry.current, 4),
            "last": round(entry.last, 4),
            "delta": round(entry.delta, 4),
            "timestamp": entry.timestamp,
        })

    return JSONResponse(content={
        "timestamp": int(time.time()),
        "count": len(result),
        "sensors": result
    })


# =================================================================
# API: Stundenwerte der letzten 24h
# =================================================================
@router.get("/hourly")
async def get_hourly_recent():
    """Liefert die Stundenwerte der letzten 24h aus hourly_values."""
    if Database._instance is None:
        return JSONResponse(content={"error": "Database not initialized"}, status_code=503)

    now = int(time.time())
    cutoff = now - 24 * 3600 # Zeitraum in Sekunden zurückrechnen
    cutoff_hour = (cutoff // 3600) * 3600

    conn = Database._instance.get_conn()
    try:
        rows = conn.execute("""
            SELECT sensor_id, hour, consumption
            FROM hourly_values
            WHERE hour >= ?
            ORDER BY hour DESC, sensor_id ASC
        """, (cutoff_hour,)).fetchall()
    finally:
        conn.close()

    sensors_info = STRUCTURE.get("sensors", {})

    # Gruppiert nach Stunde
    hours_map = {}
    for sensor_id, hour, consumption in rows:
        if hour not in hours_map:
            hours_map[hour] = {}
        hours_map[hour][sensor_id] = round(consumption, 4) if consumption else 0.0

    # Sortiert nach Stunde (neueste zuerst)
    hourly_list = []
    for hour in sorted(hours_map.keys(), reverse=True):
        sensors = hours_map[hour]
        total = round(sum(sensors.values()), 4)
        hourly_list.append({
            "hour": hour,
            "total": total,
            "sensors": sensors
        })

    # Keine Limitierung hier - cutoff_hour filtert bereits auf 24h
    # hourly_list enthält nur Stunden >= cutoff_hour

    return JSONResponse(content={
        "timestamp": now,
        "hours_count": len(hourly_list),
        "data": hourly_list
    })


# =================================================================
# API: Analytics-Zusammenfassung (Cluster-Profile)
# =================================================================
@router.get("/analytics")
async def get_analytics_summary():
    """Liefert die Cluster-Analyse aller Sensoren aus analytics.sqlite."""
    sensors_info = STRUCTURE.get("sensors", {})
    rooms_info = STRUCTURE.get("rooms", {})
    areas_info = STRUCTURE.get("areas", {})

    results = []
    for sensor_id in sorted(sensors_info.keys()):
        analytics = load_sensor_analytics(sensor_id)

        if not analytics:
            continue

        # nur Sensoren mit Verbrauch anzeigen
        if analytics.get("total", 0) <= 0:
            continue

        meta = sensors_info.get(sensor_id, {})
        room_id = meta.get("room", "")
        room_data = rooms_info.get(room_id, {})
        room_name = room_data.get("name", "-")
        area_id = room_data.get("area", "")
        area_name = areas_info.get(area_id, {}).get("name", "-")

        results.append({
            "id": sensor_id,
            "name": meta.get("name", sensor_id),
            "room": room_name,
            "area": area_name,
            "area_id": area_id,
            "cluster": analytics.get("cluster", "-"),
            "total": round(analytics.get("total", 0), 2),
            "base": round(analytics.get("base", 0), 2),
            "peak": round(analytics.get("peak", 0), 2),
            "load_factor": round(analytics.get("load_factor", 0), 4),
            "average": round(analytics.get("average", 0), 4),
            "samples": analytics.get("samples", 0),
        })

    return JSONResponse(content={
        "timestamp": int(time.time()),
        "count": len(results),
        "sensors": results
    })


# =================================================================
# API: Verifikation — Live-Deltas vs. DB-Werte prüfen
# =================================================================
@router.get("/verify")
async def verify_scale_factor():
    """Vergleicht die Live-Deltas (SensorStore) mit den DB-Stundenwerten.

    Zeigt für die aktuelle Stunde:
    - Raw-Delta (ohne Scale): Was der SensorStore berechnet
    - Scaled-Delta: Was in die DB geschrieben wird (× SENSOR_SCALE_FACTOR)
    - DB-Wert: Was tatsächlich in hourly_values steht
    - Scale-Factor: Der aktuelle Faktor aus der .env
    """
    from app.api.parsdecoder import _shared_store

    now = int(time.time())
    current_hour = (now // 3600) * 3600

    store_data = _shared_store.get_all()
    scale = settings.SENSOR_SCALE_FACTOR

    # DB-Werte für aktuelle Stunde
    db_values = {}
    if Database._instance:
        conn = Database._instance.get_conn()
        rows = conn.execute(
            "SELECT sensor_id, consumption, total FROM hourly_values WHERE hour = ?",
            (current_hour,)
        ).fetchall()
        conn.close()
        for sid, consumption, total in rows:
            db_values[sid] = {"consumption": consumption, "total": total}

    sensors = []
    for sensor_id in sorted(store_data.keys()):
        entry = store_data[sensor_id]
        if entry.current == 0:
            continue

        raw_delta = entry.delta
        scaled_delta = round(raw_delta * scale, 6)
        db = db_values.get(sensor_id, {})

        sensors.append({
            "id": sensor_id,
            "current_total": round(entry.current, 2),
            "raw_delta": raw_delta,
            "scaled_delta": scaled_delta,
            "db_consumption": db.get("consumption"),
            "db_total": db.get("total"),
        })

    return JSONResponse(content={
        "timestamp": now,
        "current_hour": current_hour,
        "scale_factor": scale,
        "info": "raw_delta × scale_factor = scaled_delta → in DB geschrieben",
        "sensors": sensors
    })

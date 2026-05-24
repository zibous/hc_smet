# -*- coding: utf-8 -*-
"""
MiScale POST Endpoint.
ESP32 sendet Waage-Daten → User erkennen → berechnen → DB → MQTT.
Debounce: Sammelt Messungen pro User, verarbeitet nach 30s Ruhe.
"""

import logging
import re
import threading

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.core.config import cfg
from app.core.webhook import notify_ha
from app.models.person import UserProfile
from app.services.calcdata import CalcData

log = logging.getLogger(__name__)

router = APIRouter()

# Services – werden von main.py injiziert
_user_service = None
_db = None
_mqtt = None

# Debounce
_pending: dict[str, dict] = {}
DEBOUNCE_SECONDS = 30


def init_services(user_service, db, mqtt_client):
    global _user_service, _db, _mqtt
    _user_service = user_service
    _db = db
    _mqtt = mqtt_client


def _normalize_ts(ts: str) -> str:
    if not ts:
        return ""
    ts = ts.strip()
    m = re.match(r"(\d{4}-\d{2}-\d{2})[T ](\d{2}:\d{2}:\d{2})", ts)
    if m:
        return f"{m.group(1)}T{m.group(2)}"
    m = re.match(r"(\d{4}-\d{2}-\d{2})", ts)
    if m:
        return f"{m.group(1)}T00:00:00"
    return ts[:19]


def _process_measurement(user_key: str):
    """Wird nach DEBOUNCE_SECONDS ohne neue Messung aufgerufen."""
    entry = _pending.pop(user_key, None)
    if not entry:
        return

    user: UserProfile = entry["user"]
    weight = entry["weight"]
    impedance = entry["impedance"]
    timestamp = entry["timestamp"]
    user_id = entry["id"]

    log.info("Verarbeite: user=%s weight=%.2f impedance=%d", user.name, weight, impedance)

    calc = CalcData(user, weight, impedance, timestamp)
    body_data = calc.calculate()
    scores_data = calc.calculate_scores()

    if _db:
        _db.upsert(user_id, body_data)

    calc.save_reference()

    if _mqtt and _mqtt.ready:
        try:
            _mqtt.publish(f"{cfg.mqtt.topic}/{user.name}/data", body_data, retain=True)
            if scores_data and "score" in scores_data:
                _mqtt.publish(f"{cfg.mqtt.topic}/{user.name}/scores", scores_data, retain=True)
            log.info("MQTT publiziert für %s", user.name)
        except Exception:
            log.exception("MQTT publish fehlgeschlagen")

    notify_ha(
        "measurement",
        user=user.name,
        weight=weight,
        impedance=impedance,
        bmi=body_data.get("bmi"),
        body_fat=body_data.get("fat"),
        muscle_mass=body_data.get("muscle"),
        water=body_data.get("water"),
    )


@router.post("/miscale")
async def miscale(request: Request):
    """ESP32 POST Handler."""
    data = await request.json()
    if not data:
        return JSONResponse({"error": "invalid JSON"}, status_code=400)

    weight = data.get("weight")
    impedance = data.get("impedance")

    if weight is None or impedance is None:
        return JSONResponse({"error": "missing weight or impedance"}, status_code=400)

    weight = float(weight)
    impedance = int(impedance)

    if weight <= 0 or impedance <= 0:
        return JSONResponse({"error": "invalid weight or impedance"}, status_code=400)

    # User erkennen
    user = None
    if data.get("name") and _user_service:
        user = _user_service.find_by_name(data["name"])
    if not user and _user_service:
        user = _user_service.find_best_by_weight(weight)
    if not user:
        log.warning("Kein User gefunden für weight=%.2f", weight)
        notify_ha("unknown_user", weight=weight, name=data.get("name", ""))
        return JSONResponse({"status": "ignored", "reason": "unknown user"})

    log.info("Messung empfangen: user=%s weight=%.2f impedance=%d", user.name, weight, impedance)

    # Debounce
    key = user.name.lower()
    if key in _pending and _pending[key].get("timer"):
        _pending[key]["timer"].cancel()

    user_id = 0
    if _user_service:
        try:
            user_id = next(
                (i + 1 for i, u in enumerate(_user_service.all_users()) if u.name.lower() == user.name.lower()), 0
            )
        except Exception:
            pass

    _pending[key] = {
        "user": user,
        "id": user_id,
        "weight": weight,
        "impedance": impedance,
        "timestamp": _normalize_ts(data.get("timestamp", "")),
        "timer": threading.Timer(DEBOUNCE_SECONDS, _process_measurement, args=[key]),
    }
    _pending[key]["timer"].daemon = True
    _pending[key]["timer"].start()

    return {"status": "ok", "user": user.name, "weight": weight}

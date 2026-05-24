import time
from pydantic import BaseModel, Field, model_validator
from typing import Any

class SensorStateEntry(BaseModel):
    """Struktur eines gespeicherten Sensors im Store (sensor_state.json)"""
    current: float | int
    last: float | int
    delta: float | int = 0
    timestamp: int

class IncomingSensorData(BaseModel):
    """Normalisiert eingehende Sensorwerte vollautomatisch."""
    current: float | int
    timestamp: int = Field(default_factory=lambda: int(time.time()))

    @model_validator(mode="before")
    @classmethod
    def normalize_input(cls, data: Any) -> Any:
        # Fall 1: Daten kommen als reiner Zahlenwert reingeflogen
        if isinstance(data, (int, float)):
            return {"current": data}

        # Fall 2: Daten kommen als Dictionary
        if isinstance(data, dict):
            current = data.get("current")
            ts = data.get("timestamp")

            # Zeitstempel reparieren (Millisekunden zu Sekunden konvertieren)
            if ts is not None:
                ts = int(ts)
                if ts > 9999999999:
                    ts //= 1000
                return {"current": current, "timestamp": ts}

        return data

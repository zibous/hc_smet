import yaml
from app.core.app_config import settings
from app.schemas.house import HouseTopology  # Das Pydantic Schema importieren

def load_house_yaml() -> dict:
    """Lädt die Haus-Topologie direkt über den zentralen Settings-Pfad
    und validiert sie im Hintergrund über Pydantic v2.
    """
    yaml_path = settings.mapping_file

    if not yaml_path.exists():
        raise FileNotFoundError(f"Kritischer Fehler: Topologie-Datei nicht gefunden unter {yaml_path}")

    with open(yaml_path, "r", encoding="utf-8") as f:
        # 🔧 1. Schritt: YAML roh einlesen und in Variable zwischenspeichern
        raw_data = yaml.safe_load(f)

    try:
        # 🔧 2. Schritt: Im Hintergrund validieren (schmeißt Fehler, wenn YAML strukturell kaputt ist)
        validated_model = HouseTopology.model_validate(raw_data)

        # 🔧 3. Schritt: Wieder als normales Dictionary zurückgeben, damit alter Code nicht bricht
        return validated_model.model_dump()

    except Exception as e:
        # Fängt Fehler ab, falls in der house.yaml z.B. Felder oder IDs fehlen
        import logging
        logging.getLogger(__name__).error(f"❌ Topologie-Validierung fehlgeschlagen! Überprüfe die house.yaml: {e}")
        raise RuntimeError(f"Ungültige house.yaml Struktur: {e}")


# Einmalig beim Starten ausführen und im Speicher halten
STRUCTURE = load_house_yaml()


def get_children(node: str) -> list[dict]:
    """Liefert die Kinder-Knoten für die hierarchische Dashboard-Navigation."""
    result = []

    # HOME -> AREAS
    if node == "HOME":
        for area_id, area in STRUCTURE.get("areas", {}).items():
            result.append({
                "id": area_id,
                "name": area["name"],
                "type": "area"
            })
        return result

    # AREA -> ROOMS
    if node in STRUCTURE.get("areas", {}):
        for room_id, room in STRUCTURE.get("rooms", {}).items():
            if room.get("area") == node:
                result.append({
                    "id": room_id,
                    "name": room["name"],
                    "type": "room"
                })
        return result

    # ROOM -> SENSORS
    if node in STRUCTURE.get("rooms", {}):
        for sensor_id, sensor in STRUCTURE.get("sensors", {}).items():
            if sensor.get("room") == node:
                result.append({
                    "id": sensor_id,
                    "name": sensor["name"],
                    "type": "sensor",
                    "devices": sensor.get("devices", [])
                })
        return result

    return result

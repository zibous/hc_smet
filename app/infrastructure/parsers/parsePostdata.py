import logging
from typing import Dict
from urllib.parse import parse_qs, urlparse

from app.core.validator import validate_sensor_value

logger = logging.getLogger(__name__)

def get_postData(data: str, index: int = 1) -> Dict[str, float]:
    """Parst die eingehenden PoKeys-Sensordaten unfehlbar für Live-Hardware (Sxx)

    UND Simulator-Formate (pxx) mit Listen-Extraktion.
    """
    try:
        data_str = str(data).replace("data=", "")

        # PoKeys trennt Parameter mit Semikolon (;), urllib erwartet aber Ampersand (&)
        sanitized_query = data_str.replace(";", "&")

        # Nutzen von urlparse und parse_qs, um die Key-Value-Paare sicher zu extrahieren
        parsed = parse_qs(urlparse("/?" + sanitized_query).query)

        sensors = {}

        for key, value in parsed.items():

            # 🔧 HYBRIDER WÄCHTER: Akzeptiert sowohl S-Keys (Live) als auch p-Keys (Test/Simulator)
            if not key.startswith("S"):
                logger.warning(f"⚠️ Falscher Sensor {key} im Telegramm")
                continue

            # 🔧 FALL 1: Echte Live-Hardware sendet bereits fertige S-Keys (z.B. S01, S26)
            if key.startswith("S"):
                sensor_id = key

            # 🔧 FALL 2: Simulator/Test ???
            else:
                try:
                    local_sensor_num = int(key[1:])
                except ValueError:
                    continue
                global_sensor_num = local_sensor_num + (index - 1)
                sensor_id = f"S{global_sensor_num:02d}"

            try:
                # Extrahiert den String aus der parse_qs-Liste und konvertiert in float
                if isinstance(value, list) and len(value) > 0:
                    sensor_value = float(value[0])
                else:
                    sensor_value = float(value)
            except (ValueError, IndexError, TypeError) as e:
                logger.warning(f"⚠️ Konvertierungsfehler für {sensor_id} bei Wert '{value}': {e}")
                continue

            # Validierung über deine Core-Logik laufen lassen
            is_valid, validated_value, error_msg = validate_sensor_value(sensor_value)
            if not is_valid:
                continue

            # Speichert die echte, nackte Kommazahl
            sensors[sensor_id] = validated_value

        return sensors

    except Exception as e:
        logger.error(f"🚨 Schwerwiegender Fehler beim Parsen der Post-Daten: {e}", exc_info=True)
        return {}

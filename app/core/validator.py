import logging
from typing import Any

logger = logging.getLogger(__name__)

def validate_sensor_value(value: Any) -> tuple[bool, float, str]:
    """
    Validiert einen Sensor-Wert und konvertiert ihn in einen float.

    Args:
        value: Zu validierender Wert (beliebiger Typ)

    Returns:
        tuple[bool, float, str]:
            - is_valid: True wenn Wert gültig
            - validated_value: Konvertierter float-Wert (0.0 bei Fehler)
            - error_message: Fehlermeldung (leer bei Erfolg)

    Regeln:
        - Muss in eine Zahl konvertierbar sein
        - Darf nicht negativ sein
        - Darf nicht > 1.000.000 sein (unrealistisch hohe Werte ablehnen)
    """
    # Robustheit: Versuchen, den Wert zu konvertieren (fängt auch Strings wie "123.45" ab)
    try:
        numeric_value = float(value)
    except (ValueError, TypeError):
        return False, 0.0, f"Invalid type or non-numeric value: {type(value)} ({value})"

    # Negative Werte ablehnen
    if numeric_value < 0:
        return False, 0.0, f"Negative value: {numeric_value}"

    # Unrealistisch hohe Werte ablehnen (> 1 Million)
    if numeric_value > 1_000_000:
        return False, 0.0, f"Unrealistic value: {numeric_value}"

    # Alles OK - float-Wert zurückgeben
    return True, numeric_value, ""

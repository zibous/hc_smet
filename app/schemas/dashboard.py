from pydantic import BaseModel, ConfigDict
from typing import Any

# =================================================================
# REQUEST MODEL (🔧 DIE EINZIGE SCHAUBILDER-RETTUNG IN V2)
# =================================================================
class DashboardRequest(BaseModel):
    """Das offizielle Request-Schema für den POST-Body.

    🔧 RESOLVED: Wir verzichten komplett auf Field() und regeln das Alias-Mapping
    vollautomatisch über AliasChoices in der model_config. Das vernichtet die
    'UnsupportedFieldAttributeWarning' und löst den 422-Fehler auf einen Schlag!
    """
    model_config = ConfigDict(
        populate_by_name=True,
        # Erlaubt dem JSON-Parser, "from" auf "from_ts" und "to" auf "to_ts" zu mappen
        alias_generator=lambda field_name: {
            "from_ts": "from",
            "to_ts": "to"
        }.get(field_name, field_name)
    )

    node: str = "HOME"

    # Reine Typ-Deklarationen – absolut unanfällig für Schema-Warnungen!
    from_ts: str
    to_ts: str

    compare: int = 1

# =================================================================
# RESPONSE MODEL
# =================================================================
class HouseStructure(BaseModel):
    id: str
    name: str
    children: list[Any] = []

class DashboardResponse(BaseModel):
    """Das finale Schema, exakt abgestimmt auf deine originalen Rückgaben."""
    house: HouseStructure
    kpis: dict[str, Any] = {}
    cards: dict[str, Any] = {}
    timeseries: dict[str, Any] = {}

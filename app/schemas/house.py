from pydantic import BaseModel, Field, RootModel

# =================================================================
# Level 3: HOUSE
# =================================================================
class HouseConfig(BaseModel):
    name: str
    includes: list[str] = Field(default_factory=list)

class HouseMap(RootModel[dict[str, HouseConfig]]):
    """Sammelt alle Häuser (z.B. {"HOME": HouseConfig})"""
    pass

# =================================================================
# Level 2: AREAS
# =================================================================
class AreaConfig(BaseModel):
    name: str

class AreaMap(RootModel[dict[str, AreaConfig]]):
    """Sammelt alle Bereiche (z.B. {"EG": AreaConfig})"""
    pass

# =================================================================
# Level 1: ROOMS
# =================================================================
class RoomConfig(BaseModel):
    name: str
    area: str

class RoomMap(RootModel[dict[str, RoomConfig]]):
    """Sammelt alle Räume (z.B. {"EG_R01": RoomConfig})"""
    pass

# =================================================================
# Level 0: SENSORS
# =================================================================
class SensorConfig(BaseModel):
    name: str
    room: str
    devices: list[str] = Field(default_factory=list)

class SensorMap(RootModel[dict[str, SensorConfig]]):
    """Sammelt alle Sensoren (z.B. {"S01": SensorConfig})"""
    pass

# =================================================================
# Das Haupt-Dokument (Das YAML-File)
# =================================================================
class HouseTopology(BaseModel):
    """Bildet die gesamte house.yaml Validierung ab"""
    house: dict[str, HouseConfig]
    areas: dict[str, AreaConfig]
    rooms: dict[str, RoomConfig]
    sensors: dict[str, SensorConfig]

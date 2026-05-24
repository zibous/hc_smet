# PYTHONPATH=. pyreverse app/*.py app/**/*.py -o mmd -p EnergieApp

classDiagram
  direction TR

  %% --- SERVICES & CORE ---
  class SensorService {
    aggregator : EnergyAggregator, NoneType
    store
    get_all()
    handle(device: str, payload: Any, simulator: bool, skip_db: bool) dict[str, dict]
  }

  class EnergyAggregator {
    db : NoneType
    lock : lock
    cleanup(retention_days: int)
    process(sensor_id: str, current_value: float, timestamp: int)
  }

  class DashboardService {
    db : Database, NoneType
    get_current(node: str, start: datetime, end: datetime, freq: str) dict
  }

  class MQTTClient {
    auth : dict | None
    client_id : str
    host : str
    logger : NoneType, RootLogger
    port : int
    publish(payload, topic: str, qos: int, retain: bool, keepalive: int, loginfo: bool) None
  }

  class Webhook {
    base_url
    timeout : int
    url
    webhook_id : str
    send(data: Optional[Dict[str, Any]]) bool
  }

  %% --- SCHEMAS & DATA STRUCTURES ---
  class IncomingSensorData {
    current : float | int
    timestamp : int
    normalize_input(data: Any) Any
  }

  class SensorStateEntry {
    current : float | int
    delta : float | int
    last : float | int
    timestamp : int
  }

  class DashboardRequest {
    compare : int
    from_ts : str
    model_config
    node : str
    to_ts : str
  }

  class DashboardResponse {
    cards : dict[str, Any]
    house
    kpis : dict[str, Any]
    timeseries : dict[str, Any]
  }

  %% --- TOPOLOGY & CONFIG ---
  class HouseTopology {
    areas : dict[str, AreaConfig]
    house : dict[str, HouseConfig]
    rooms : dict[str, RoomConfig]
    sensors : dict[str, SensorConfig]
  }
  class AreaConfig { name : str }
  class RoomConfig { area : str, name : str }
  class SensorConfig { devices : list[str], name : str, room : str }
  class HouseConfig { includes : list[str], name : str }

  class HouseStructure {
    children : list[Any]
    id : str
    name : str
  }

  class Settings {
    APP_NAME : str
    DB_PATH : Path
    MQTT_HOST : str
    analytics_db_path
    database_path
    sensor_devices
    get_device(name: str) dict[str, Any] | None
    get_devices_start_index(name: str) int
    get_timestamp_iso(ts: Any) str
  }
  class SettingsSchema { model_config }

  class AreaMap
  class HouseMap
  class RoomMap
  class SensorMap

  %% =====================================================
  %% ✨ RELATIONSHIPS & DEPENDENCIES (DIAGRAMMPFEILE)
  %% =====================================================
  SensorService --> EnergyAggregator : steuert an
  SensorService ..> IncomingSensorData : validiert mit
  SensorService --> SensorStateEntry : trackt Zustand im RAM

  DashboardService ..> DashboardRequest : verarbeitet
  DashboardService ..> DashboardResponse : erzeugt
  HouseStructure --* DashboardResponse : house

  HouseTopology --* AreaConfig : besitzt
  HouseTopology --* RoomConfig : besitzt
  HouseTopology --* SensorConfig : besitzt
  HouseTopology --* HouseConfig : besitzt

  Settings --|> SettingsSchema : erweitert/erfüllt
  AreaMap --|> AreaConfig
  HouseMap --|> HouseConfig
  RoomMap --|> RoomConfig
  SensorMap --|> SensorConfig

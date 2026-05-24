# Smartmeters Dashboard

## Ablauf

```bash

       [📡 PoKeys-Gerät (IF64/IF65) oder Simulator]
                     │
                     │  1. HTTP POST (z.B. "data=p1=4500;p2=1200")
                     ▼
 ┌────────────────────────────────────────────────────────┐
 │ 1. HTTP-EINGANGSTÜR: app/api/parsdecoder.py            │
 ├────────────────────────────────────────────────────────┤
 │ • Liest Header (User-Agent, X-Source)                  │
 │ • Extrahiert den rohen Body-String                     │
 │ • Erzeugt SensorService via Dependency Injection       │
 └───────────────────┬────────────────────────────────────┘
                     │
                     │ 2. Reicht rohen String + Device-Name weiter
                     ▼
 ┌────────────────────────────────────────────────────────┐
 │ 2. SCHALTZENTRALE: app/services/sensor_service.py      │
 └───────────────────┬────────────────────────────────────┘
                     │
                     ├─► (A) Ruft Parser auf ─────────────────┐
                     │                                        ▼
                     │                 ┌──────────────────────────────────────────────┐
                     │                 │ 3. PARSER: app/infrastructure/parsers/       │
                     │                 │    parsePostdata.py                          │
                     │                 ├──────────────────────────────────────────────┤
                     │                 │ • Säubert String (";" → "&")                 │
                     │                 │ • Berechnet globale IDs (p1 → S01)           │
                     │                 │ • Validiert Werte (core/validator.py)        │
                     │                 └──────────────────────┬───────────────────────┘
                     │                                        │
                     │  Gibt Dict zurück: {"S01": 4500.2, ...}│
                     │◄───────────────────────────────────────┘
                     │
                     ├─► (B) Validiert via Pydantic (schemas/sensors.py)
                     │
                     ├─► (C) Aktualisiert SensorStore ───────────┐
                     │                                           ▼
                     │                 ┌──────────────────────────────────────────────┐
                     │                 │ 4. RAM-SPEICHER: app/services/state/         │
                     │                 │    sensor_store.py                           │
                     │                 ├──────────────────────────────────────────────┤
                     │                 │ • Prüft ob sensor_state.json existiert       │
                     │                 │   ├─ NEIN: Erststart-Kalibrierung (delta=0)  │
                     │                 │   └─ JA: Lädt alten Stand                    │
                     │                 │ • Speichert: current, last, delta, timestamp │
                     │                 │ • Erkennt Zähler-Resets (current < last)     │
                     │                 │ • Persistiert nach sensor_state.json         │
                     │                 └──────────────────────┬───────────────────────┘
                     │                                        │
                     │◄───────────────────────────────────────┘
                     │
                     ├─► (D) Übergibt absoluten Zählerstand an Aggregator
                     ▼
 ┌────────────────────────────────────────────────────────┐
 │ 5. AGGREGATOR: app/services/energy_aggregator.py       │
 ├────────────────────────────────────────────────────────┤
 │ • Holt letzten Stand aus DB-Tabelle sensor_state       │
 │ • Berechnet Delta: current_value - last_value          │
 │ • Verteilt Delta zeitgewichtet auf Stunden             │
 │ • Schreibt in hourly_values (sensor_id, hour, consumption)
 │ • Aktualisiert sensor_state mit neuem Zählerstand      │
 └───────────────────┬────────────────────────────────────┘
                     │
                     ▼
 ┌────────────────────────────────────────────────────────┐
 │ 6. DATENBANK: app/infrastructure/database/dbconnect.py │
 ├────────────────────────────────────────────────────────┤
 │ • SQLite Singleton (WAL-Modus, thread-safe)            │
 │ • Jahres-Datenbanken: data/sensors_YYYY.db             │
 │ • Tabellen: sensor_state, hourly_values                │
 └────────────────────────────────────────────────────────┘


 ═══════════════════════════════════════════════════════════
  DASHBOARD (Lese-Pfad)
 ═══════════════════════════════════════════════════════════

       [🌐 Browser]
            │
            │  GET / POST /api/dashboard
            ▼
 ┌────────────────────────────────────────────────────────┐
 │ app/api/dashboard.py                                   │
 │ → DashboardResponseBuilder (builders/dashboard_builder)│
 │ → DashboardService (services/dashboard_service)        │
 │ → energy_repository.py (SQL-Abfrage über Jahre)        │
 │ → data_builder.py (KPIs, Cards, Timeseries)            │
 └────────────────────────────────────────────────────────┘
            │
            │  Nutzt Haus-Topologie: app/domain/house.yaml
            │  Nutzt Analytics: data/analytics.sqlite
            ▼
       [📊 JSON Response → Chart.js Frontend]

```

## Projektstruktur

```
hc_smet/
├── app/
│   ├── main.py                  # FastAPI App + Lifespan
│   ├── api/                     # Router (base, dashboard, dashboard2, parsdecoder, settingsdata)
│   ├── core/                    # app_config.py (Pydantic Settings), Middleware, Logging
│   ├── domain/                  # house.yaml + house.py (Topologie)
│   ├── infrastructure/
│   │   ├── builders/            # Dashboard Response Builder, Data Builder
│   │   ├── database/            # DB-Singleton, Repositories, Analytics Repository
│   │   └── parsers/             # PoKeys POST-Daten Parser
│   ├── schemas/                 # Pydantic Models (sensors, house, settings)
│   └── services/                # SensorService, MQTTPublisher, SensorStore
│       └── state/               # SensorStore (RAM + JSON Persistenz)
├── frontend/
│   ├── static/
│   │   ├── css/                 # style.css, live.css
│   │   └── js/                  # main.js, live/ (sensors, hourly, analytics)
│   └── templates/               # Jinja2 HTML (index, index2, status, settings)
├── data/                        # SQLite DBs (sensors_YYYY.db, analytics.sqlite)
├── analytics/                   # Analytics-Daemon (Clustering, Tagesprofile)
├── scripts/                     # Import-Scripts (getpokey_data, import_from_server)
├── tests/
│   └── v3/                      # Pytest Tests (app_config, mqtt, sensor_store, etc.)
├── docker-compose.yml
├── Dockerfile
└── Makefile
```

## Wichtige Änderungen (v2.2.0)

### ✅ Neue Konfiguration (app_config.py)
- **Pydantic Settings** statt manuelles `os.getenv()`
- **Nested Models**: `PokeyDevice`, `DeviceConfig`, `InterfaceConfig`
- **Cached Properties** für Performance
- **100% Rückwärtskompatibel** - alle alten Properties funktionieren
- **Type Safety** - vollständige Type Hints

### ✅ MQTT Home Assistant Discovery
- **Automatische Discovery** beim MQTT-Connect
- **Hierarchische Struktur**: Haus → Areas → Räume → Sensoren
- **Device Config** aus `settings.device`
- Methoden: `publish_discovery()`, `unpublish_discovery()`

### ✅ Frontend Verbesserungen
- **Live Dashboard** (index2.html) mit 3 Tabs:
  - 📡 Live Sensoren (gruppiert nach Geschoss)
  - ⏱️ Stundenwerte 24h (Chart + Tabelle)
  - 🔬 Analytics (Sensor-Profile/Clustering)
- **Navigation** zwischen Dashboard und Live
- **Hintergrundfarbe-Picker** mit localStorage
- **Area-Gruppierung** (EG, WG, OG, DG, OS, NU)

### ✅ Test-Suite (pytest)
- **90+ Tests** in `tests/v3/`
- Tests für: app_config, mqtt_publisher, sensor_store, sensor_service, settingsdata
- **Makefile Targets**: `make test-v3`, `make test-config`
- Alle Tests berücksichtigen `SENSOR_SCALE_FACTOR`

## Konfiguration

Die Konfiguration erfolgt über `.env` Datei und wird von `app/core/app_config.py` geladen:

```bash
# Application
APP_NAME=pokeys-service
SERVER_PORT=8096

# Data Mode
POKEY_SERVICE=POST
SENSOR_SCALE_FACTOR=0.1

# Database
DB_PATH=data/
DB_ENABLED=true

# MQTT
MQTT_ENABLED=true
MQTT_HOST=10.1.1.119
MQTT_PORT=1883
MQTT_TOPIC_BASE=smartmeters

# PoKeys Devices
POKEYS_DEVICE1_ID=IF64
POKEYS_DEVICE1_IP=10.1.1.64
POKEYS_DEVICE1_SENSORS=1-25

POKEYS_DEVICE2_ID=IF65
POKEYS_DEVICE2_IP=10.1.1.65
POKEYS_DEVICE2_SENSORS=26-50
```

## Makefile Commands

```bash
# Docker
make up              # Start containers
make down            # Stop containers
make restart         # Restart containers
make logs            # Show logs

# Development
make run             # Start local with uvicorn
make dev             # Start with auto-reload

# Testing
make test-v3         # Run all v3 tests
make test-config     # Test app_config only
make validate        # Run all tests

# Cleanup
make clean           # Remove cache files
```

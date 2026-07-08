# hc_smet – Smart Meters (50 S0-Stromzähler Dashboard)

Granulare Stromverbrauchsmessung auf Raum- und Geräteebene mit 50 S0-Impulszählern, zwei PoKeys57E Ethernet-Controllern und einem FastAPI-Dashboard – inklusive 13 Jahre Messhistorie.

## Features

- ⚡ **50 S0-Stromzähler** – Individueller Verbrauch pro Raum/Gerät
- 🔌 **2× PoKeys57E** – Ethernet I/O Controller (je 25 Sensoren)
- 📊 **Hierarchische Aggregation** – Sensor → Raum → Bereich → Haus
- 📈 **Langzeit-Archiv** – Jahr-basierte SQLite DBs seit 2013
- 🔄 **Zwei Betriebsmodi** – POST (Station sendet) oder GET (App pollt)
- 🧮 **Periodenberechnung** – Tag/Woche/Monat/Jahr + Vorperioden
- 📡 **MQTT Publishing** – Sensoren, Räume, Bereiche, Haus
- 🏠 **HA Discovery** – Automatische Sensor-Registrierung
- 🔔 **Webhooks** – Heartbeat, Tages-/Monatssummary
- 💰 **Kostenberechnung** – Strompreis × Verbrauch pro Sensor
- 📉 **Jahresvergleich** – Chart.js Visualisierung 2013–2026
- 🐳 **Docker-ready** – mit Graceful Shutdown

## Application Workflow

```
┌───────────────────────────────────────────────────────────────────────────┐
│                         main.py (Lifespan)                                │
│  1. Database init  2. PoKeys Manager  3. MQTT Publisher  4. Webhooks      │
└────────────┬──────────────────────────────────────────────────────────────┘
             │
     ┌───────┴────────────────────────────────────────┐
     │                                                │
     ▼                                                ▼
┌─────────────────────────────┐         ┌──────────────────────────────────┐
│  Sensor-Datenerfassung      │         │  FastAPI Server (Port 8096)      │
│                             │         ├──────────────────────────────────┤
│  Modus POST:                │         │  /api/status                     │
│    PoKeys → HTTP POST →App  │         │  /api/sensors                    │
│                             │         │  /api/sensor/{id}                │
│  Modus GET:                 │         │  /api/room/{id}                  │
│    App pollt PoKeys (5min)  │         │  /api/area/{id}                  │
│    GET /sensorList.json     │         │  /api/home                       │
└──────────────┬──────────────┘         │  /api/dashboard                  │
               │                        │  /api/yearly                     │
               ▼                        │  /api/kpidata                    │
┌─────────────────────────────┐         │  / (Dashboard SPA)              │
│  SensorService              │         │  /live (Live Dashboard)          │
│  • Normalisierung           │         └──────────────┬───────────────────┘
│  • Reset-Erkennung          │                        │
│  • Delta-Berechnung         │                        ▼
│  • Validierung              │         ┌──────────────────────────────────┐
└──────────────┬──────────────┘         │  DashboardService                │
               │                        │  • Zeitreihen (stündlich)        │
               ▼                        │  • Vergleichszeiträume           │
┌─────────────────────────────┐         │  • KPI-Cards                    │
│  EnergyAggregator           │         └──────────────────────────────────┘
│  • Stundenwerte aggregieren │
│  • DB Upsert (Thread-safe)  │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐     ┌────────────────────────────────────┐
│  SQLite DB (pro Jahr)       │     │  HouseTopology (house.yaml)        │
│  sensors_2026.db            │     │  • 50 Sensoren                     │
│  ├── current_values         │     │  • 20 Räume                        │
│  └── hourly_values          │     │  • 6 Bereiche (EG,WG,OG,DG,OS,NU) │
└──────────────┬──────────────┘     │  • 1 Haus (HOME)                   │
               │                    └────────────────────────────────────┘
               ▼
┌─────────────────────────────┐     ┌────────────────────────────────────┐
│  Calculator (on-demand)     │     │  MQTT Publisher                    │
│  • Tages-/Wochen-/Monats-  │     │  smartmeters/sensors/{id}          │
│    /Jahresverbrauch         │     │  smartmeters/rooms/{id}            │
│  • Vorperioden-Vergleich    │     │  smartmeters/areas/{id}            │
│  • Raum/Bereich/Haus-Aggr. │     │  smartmeters/home                  │
└─────────────────────────────┘     │  (alle 5 Minuten)                 │
                                    └────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────┐
│  Webhook Publisher → HA     │
│  • heartbeat (5min)         │
│  • daily_summary (0:00)     │
│  • monthly_summary (1.)     │
│  • app_start / app_stop     │
└─────────────────────────────┘
```

## Hardware

### PoKeys57E Ethernet Controller

| Gerät | IP | Sensoren | Standort |
|-------|-----|----------|----------|
| **poKey64** | 10.1.1.64 | S01–S25 | Zählerschrank EG |
| **poKey65** | 10.1.1.65 | S26–S50 | Zählerschrank EG |

- **Hersteller**: PoLabs d.o.o, Ljubljana, Slovenien
- **Modell**: PoKeys57E – Ethernet I/O Controller
- **Protokoll**: HTTP JSON (`/sensorList.json`)

### S0-Stromzähler

- **50 Stück** – jeder Raum/Großverbraucher hat einen eigenen Zähler
- **Modelle**: eacWSZ-50A (1000 Imp/kWh), eacDSZ-63A (800 Imp/kWh)
- **Verteilung**: Kellergeschoss, Wohngeschoss, Obergeschoss, Dachgeschoss, Außen

## Haus-Topologie (50 Sensoren)

```
HOME (Haus-Gesamt)
├── EG (Kellergeschoss)
│   ├── Büro (S32)
│   ├── Wirtschaftsraum (S01 Licht, S02 Heizung, S03 Pumpe, S34 Boiler, S36 Waschen)
│   ├── Vorratsraum (S05 Tiefkühltruhe)
│   ├── Gang (S04)
│   └── Zählerschrank (S06 Technik, S30 Geräte, S37 Netzteil)
├── WG (Wohngeschoss)
│   ├── Eingang (S49)
│   ├── Gäste WC (S07)
│   ├── Küche (S08 Geräte, S09 Licht, S12 Möbel, S13 Kühlschrank, S14, S15 Spülmaschine, S35 Herd)
│   ├── Wohnzimmer (S10 Verbraucher, S11 Media)
│   └── Wintergarten (S48)
├── OG (Obergeschoss)
│   ├── Flur (S16)
│   ├── Bad (S33)
│   ├── Zimmer Tina (S19)
│   ├── Zimmer Gäste (S17, S18)
│   └── Schlafzimmer (S20, S25)
├── DG (Dachgeschoss)
│   ├── Fitnessraum (S21 Media, S22 Strom, S23 Wechselrichter)
│   └── Allgemein (S24, S27, S28)
└── OS (Außenbereich)
    ├── Garage (S29)
    └── Garten (S50)
```

## Betriebsmodi

| Modus | Beschreibung | Konfiguration |
|-------|-------------|---------------|
| **POST** | PoKeys sendet aktiv Daten an die App | `POKEY_SERVICE=POST` |
| **GET** | App pollt PoKeys alle 5 Minuten | `POKEY_SERVICE=GET` |

Im POST-Modus empfängt die App HTTP-POSTs von den PoKeys-Controllern. Im GET-Modus pollt ein Background-Thread die `/sensorList.json` Endpunkte.

## Datenbank

### Jahr-basierte SQLite-Dateien

```
data/
├── sensors_2013.db    # älteste Daten
├── sensors_2014.db
├── ...
├── sensors_2025.db
└── sensors_2026.db    # aktuelles Jahr
```

### Tabellen

**`current_values`** – Letzte Messwerte pro Sensor:
- sensor_id, total (kWh), current (kWh), timestamp

**`hourly_values`** – Stündliche Aggregation:
- sensor_id, hour_ts, total (kWh), consumption (kWh)

### Datenmenge

- 50 Sensoren × 24h × 365 Tage = **438.000 Stundenwerte/Jahr**
- 13 Jahre Archiv = **~5,7 Millionen Datenpunkte gesamt**
- Speicher: ~50 MB pro Jahr-DB

## API Endpoints

| Endpoint | Beschreibung |
|----------|--------------|
| `GET /api/status` | App-Status (Uptime, Post-Count, Sensor-Count) |
| `GET /api/sensors` | Alle Sensoren mit aktuellen Werten |
| `GET /api/sensor/{id}` | Einzelner Sensor mit allen Perioden |
| `GET /api/room/{id}` | Raum-Aggregation |
| `GET /api/area/{id}` | Bereich-Aggregation |
| `GET /api/home` | Haus-Gesamtverbrauch |
| `GET /api/dashboard` | Dashboard-Daten (Zeitreihen + KPIs) |
| `GET /api/yearly` | Jahresvergleich (Chart.js) |
| `GET /api/kpidata` | KPI für Übersichts-Dashboard |
| `GET /api/settings` | Haus-Topologie + Config |
| `POST /postdata` | Sensor-Daten empfangen (POST-Modus) |
| `GET /` | Dashboard (HTML) |
| `GET /live` | Live Dashboard |

## MQTT Topics

```
smartmeters/
├── lwt                         # online/offline
├── status                      # App-Status
├── sensors/
│   ├── S01                     # Einzelner Sensor
│   ├── S02
│   └── ...
├── rooms/
│   ├── EG_R01                  # Raum-Aggregation
│   └── ...
├── areas/
│   ├── EG                      # Bereich-Aggregation
│   └── ...
└── home                        # Haus-Gesamt
```

## Konfiguration (.env)

| Variable | Default | Beschreibung |
|----------|---------|--------------|
| `POKEY_SERVICE` | `POST` | Modus: POST oder GET |
| `SERVER_PORT` | `8096` | App-Port |
| `POKEYS_DEVICE1_IP` | `10.1.1.64` | IP PoKey64 |
| `POKEYS_DEVICE2_IP` | `10.1.1.65` | IP PoKey65 |
| `FETCH_INTERVAL` | `300` | Polling-Intervall GET-Modus (Sekunden) |
| `MQTT_ENABLED` | `false` | MQTT aktivieren |
| `MQTT_HOST` | `localhost` | MQTT Broker |
| `MQTT_INTERVAL` | `300` | MQTT Publish-Intervall |
| `DB_ENABLED` | `false` | SQLite aktivieren |
| `MAPPING_ENABLED` | `false` | Haus-Topologie aktivieren |
| `STROMPREISE` | `{"2026": 0.24}` | Strompreise pro Jahr (JSON) |
| `HA_WEBHOOK_URL` | – | Home Assistant Webhook |

## Projektstruktur

```
hc_smet/
├── app/
│   ├── main.py                     # FastAPI Entry + Lifespan
│   ├── api/
│   │   ├── base.py                 # /api/status, /api/sensors, /api/home
│   │   ├── dashboard.py            # /api/dashboard (Zeitreihen)
│   │   ├── dashboard2.py           # /live Dashboard
│   │   ├── kpi.py                  # /api/kpidata
│   │   ├── parsdecoder.py          # POST /postdata (Sensor-Empfang)
│   │   └── settingsdata.py         # /api/settings
│   ├── core/
│   │   ├── app_config.py           # Pydantic Settings + Device Models
│   │   ├── logging_setup.py        # Logger
│   │   ├── middleware.py           # CORS, NoCaching
│   │   └── webhook.py              # HA Webhook Client
│   ├── domain/
│   │   ├── house.yaml              # Haus-Topologie (Sensoren/Räume/Bereiche)
│   │   ├── house.py                # HouseTopology Parser
│   │   ├── pokey_device.py         # PoKey Device Abstraction
│   │   └── s0_sensor.py            # S0 Sensor Model
│   ├── infrastructure/
│   │   └── ...                     # DB, MQTT Low-Level
│   ├── models/
│   │   └── ...                     # Pydantic Models
│   ├── schemas/
│   │   └── kpi.py                  # KPI Response Schema
│   └── services/
│       ├── sensor_service.py       # Datenverarbeitung + Reset-Erkennung
│       ├── calcdata.py             # Periodenberechnung (Tag/Woche/Monat/Jahr)
│       ├── dashboard_service.py    # Dashboard Aggregation
│       ├── db_manager.py           # SQLite (EnergyAggregator)
│       ├── pokeys_manager.py       # PoKeys Polling (GET-Modus)
│       ├── mqtt_publisher.py       # MQTT Publish + Discovery
│       ├── ha_discovery.py         # HA Auto-Discovery Config
│       ├── kpi_service.py          # KPI-Berechnung
│       ├── webhook_builder.py      # Webhook Payload Builder
│       ├── body_metrics.py         # Körperdaten-Analyse (Fitness)
│       ├── body_scales.py          # Bewertungsskalen
│       ├── body_score.py           # Score-Berechnung
│       ├── startup.py              # Init-Logik
│       └── state/                  # RAM State Management
├── config/
│   ├── ha_discovery.yaml           # HA Discovery Templates
│   ├── persons.yaml                # Personen-Profile (Fitness)
│   └── lang/                       # i18n
├── data/
│   ├── sensors_2013.db ... sensors_2026.db  # Jahr-DBs
│   ├── analytics.sqlite            # Analytics-DB
│   └── pokeys_state.json           # Letzter State
├── frontend/
│   ├── static/js/                  # ES-Module Dashboard
│   └── templates/                  # Jinja2 HTML
├── analytics/                      # Separater Analytics-Container
├── scripts/                        # Import, Simulation, Verify
├── tests/                          # pytest
├── docker-compose.yml
├── Dockerfile
├── Makefile
└── .env
```

## Makefile

```bash
make dev            # Lokal mit auto-reload
make run            # Lokal ohne reload
make build          # Docker Image
make rebuild        # Rebuild + Restart (no-cache)
make up / down      # Docker starten/stoppen
make health         # Health Check
make reset          # DB neu vom Server + App starten
make validate       # pytest Tests
make jsbuild        # Frontend JS/CSS bundlen
make graph          # Klassendiagramm generieren
make clean          # Cache aufräumen
```

## Datenmenge & Performance

| Metrik | Wert |
|--------|------|
| Sensoren | 50 (aktiv: ~35) |
| Messungen/Tag | 14.400 (50 × 12/h × 24h) |
| Stundenwerte/Jahr | 438.000 |
| Gesamtarchiv | ~5,7 Mio. Datenpunkte (13 Jahre) |
| DB-Größe/Jahr | ~50 MB |
| MQTT Messages/Tag | ~14.000 |

## Requirements

- Python 3.10+ (getestet mit 3.12)
- 2× PoKeys57E Ethernet Controller
- 50× S0-Stromzähler (eacWSZ-50A / eacDSZ-63A)
- MQTT Broker (optional)
- Docker (optional, empfohlen)

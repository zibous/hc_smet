# Smart Meters - Verbrauchszähler System

## Architektur

```
Verbrauchszähler (Sensoren)
    ↓
HTTP POST (Rohdaten)
    ↓
app.py (Empfang + Normalisierung)
    ↓
JSON Cache (letzte Werte mit Reset-Erkennung)
    ↓
Processing Layer (Validierung + Strukturierung)
    ↓
SQLite DB (aktuelle Werte + Stundenwerte)
    ↓
Berechnung Layer (Tag, Woche, Monat, Jahr)
    ↓
    ├─→ HTTP API (JSON)
    └─→ MQTT Output (Home Assistant)
```

## Module

### 1. app.py & worker.py
- **app.py**: HTTP Server für Sensor-Daten und API
- **worker.py**: Background Worker für MQTT Publishing und Scheduler
- Beide laufen parallel und kommunizieren über SQLite DB

### 2. JSON Cache (`lib/cache.py`)
- Speichert letzte Sensor-Werte in `data/sensor_cache.json`
- **Reset-Erkennung**: Wenn `total < last_total` → Sensor wurde zurückgesetzt
- Berechnet `current` = `total - last_total`

### 3. Processing Layer (`lib/processor.py`)
- Validiert Sensor-Daten (gültig? vollständig?)
- Berechnet current-Verbrauch mit Reset-Erkennung
- Speichert in SQLite DB
- Aktualisiert HouseModel

### 4. SQLite DB (`lib/database.py`)
- **Jahr-basierte Datenbanken**: `sensors_YYYY.db` (2013-2026)
- **current_values**: Aktuelle Messwerte pro Sensor
- **hourly_values**: Stündliche Aggregationen
- Hauptdatei: `data/sensors.db` (aktuelles Jahr)

### 5. Berechnung Layer (`lib/calculator.py`)
Berechnet Verbrauch für:
- Tag / Vortag
- Woche / Vorwoche
- Monat / Vormonat
- Jahr

Aggregationen:
- Sensor-Level
- Raum-Level
- Bereich-Level (Area)
- Haus-Level (Home)

### 6. HTTP API (`lib/api.py`)

#### Endpunkte:

**Sensoren:**
- `GET /sensors` - Alle Sensoren (Übersicht)
- `GET /sensor/<id>` - Einzelner Sensor mit allen Perioden

**Aggregationen:**
- `GET /room/<id>` - Raum-Aggregation
- `GET /area/<id>` - Bereich-Aggregation
- `GET /home` - Haus-Aggregation

**Yearly Comparison:**
- `GET /yearly_comparison` - JSON mit allen Jahren
- `GET /yearly` - HTML Visualisierung mit Chart.js

**Legacy:**
- `GET /getdata` - Rohdaten (postdata.json)

#### Beispiel Response `/sensor/S01`:
```json
{
  "id": "S01",
  "name": "Wirtschaftsraum",
  "room": "Wirtschaftsraum",
  "area": "Kellergeschoss",
  "total": 768.92,
  "current": 0.04,
  "day": 0.01,
  "yesterday": 0.01,
  "week": 0.01,
  "lastweek": 0.01,
  "month": 0.01,
  "lastmonth": 0.01,
  "year": 0.01,
  "timestamp": "2026-02-06T18:34:38"
}
```

### 7. MQTT Output (`lib/mqtt_publisher.py`)

**Topics:**
- `smartmeters/lwt` - Last Will Testament (online/offline)
- `smartmeters/status` - Status mit post_count, uptime, etc.
- `smartmeters/data/<sensor_id>` - Sensor-Daten
- `smartmeters/data/room/<room_id>` - Raum-Aggregation
- `smartmeters/data/area/<area_id>` - Bereich-Aggregation
- `smartmeters/data/home` - Haus-Aggregation

**Payload Beispiel:**
```json
{
  "name": "Wirtschaftsraum",
  "id": "S01",
  "type": "sensor",
  "interface": "pokey64",
  "port": 1,
  "area": "Kellergeschoss",
  "room": "Wirtschaftsraum",
  "current": 0.04,
  "day": 0.01,
  "yesterday": 0.01,
  "week": 0.01,
  "lastweek": 0.01,
  "month": 0.01,
  "lastmonth": 0.01,
  "year": 0.01,
  "total": 768.92,
  "state": "online",
  "lastseen": "2026-02-06T17:34:38Z",
  "timestamp": "2026-02-06T18:34:38"
}
```

### 8. Scheduler (`lib/scheduler.py`)
- Läuft im worker.py
- Aggregiert stündlich die Verbrauchswerte
- Speichert in `hourly_values` Tabelle

### 9. MySQL Import (`remoute/mysqldata.py`)
- Importiert historische Daten aus MySQL
- Erstellt jahr-basierte SQLite DBs (sensors_YYYY.db)
- Spezielle Korrektur für 2025 (Faktor 0.595 wegen höherer Messfrequenz)
- Verwendung: `python mysqldata.py 2025` oder `make import-data ARGS="2025"`

## Installation

```bash
# Virtual Environment aktivieren
source .venv/bin/activate

# Dependencies installieren
pip install -r requirements.txt
```

## Konfiguration

**Umgebungsvariablen** (`.env`):
```bash
MQTT_HOST=<host>
MQTT_PORT=<port>
MQTT_USER=<user>
MQTT_PASS=<pass>
SERVER_SERVERIP=<ip>
SERVER_PORT=8095
LOG_LEVEL=INFO
```

**House Model** (`config/house.yaml`):
- Definiert Sensoren, Räume, Bereiche
- Hierarchie: Sensor → Raum → Bereich → Haus

## Starten

```bash
# Beide Prozesse starten
make start-all

# Oder einzeln
python app.py      # HTTP Server
python worker.py   # MQTT Worker
```

## Makefile Befehle

```bash
make start-all       # Startet app.py und worker.py
make stop-all        # Stoppt beide Prozesse
make restart         # Neustart
make import-data     # Importiert Daten vom Server
make import-data ARGS="2025"  # Nur 2025
make clean           # Löscht Cache
make help            # Zeigt alle Befehle
```

## Datenfluss

1. **Sensor sendet POST** → `app.py` empfängt Rohdaten
     Test pokey1: http://10.1.1.64/sensorList.json
     Test pokey2: http://10.1.1.65/sensorList.json
2. **Normalisierung** → Rohdaten werden in einheitliches Format gebracht
3. **JSON Cache** → Letzte Werte werden gespeichert (Reset-Erkennung)
4. **Processing** → Validierung + current-Berechnung
5. **SQLite DB** → Persistente Speicherung
6. **Stündlich** → Scheduler aggregiert Stundenwerte
7. **API/MQTT** → Daten werden bereitgestellt

## Sensor Reset

Wenn ein Sensor zurückgesetzt wird (`total < last_total`):
- Cache erkennt automatisch den Reset
- `current` wird auf `total` gesetzt (nicht negativ)
- Nächster Wert wird wieder normal berechnet

## Yearly Comparison

- Visualisiert Jahresverbrauch 2013-2026
- Chart.js Bar Chart mit Jahr-über-Jahr Vergleich
- Zeigt Differenzen und prozentuale Änderungen
- URL: http://10.1.1.40:2705/yearly

## Effizienz für 50 Sensoren

- **Alle 5 Minuten**: 50 Sensoren × 12/h × 24h = 14.400 Messungen/Tag
- **SQLite**: Effizient für diese Datenmenge
- **Stundenwerte**: Reduziert Datenmenge für Langzeit-Analysen
- **Jahr-basierte DBs**: Verhindert Datenverlust, verbessert Performance
- **Aggregationen**: Werden on-demand berechnet (nicht gespeichert)

## Erweiterungen

### Manueller Sensor Reset
```python
from lib.cache import SensorCache
cache = SensorCache('data/sensor_cache.json')
cache.reset('S01')  # Reset Sensor S01
```

### Eigene Aggregationen
```python
from lib.calculator import Calculator
calc = Calculator('data/sensors.db', house)
verbrauch = calc.calculate_period('S01', 'week')
```

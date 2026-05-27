# Migration: POST → GET (NetworkClient)

## Projekt: `apps_v2/hc_smet`

**Datum:** 2026-05-26  
**Status:** ✅ IMPLEMENTIERT  
**Modus:** `POKEY_SERVICE=GET` (Testphase: `FETCH_INTERVAL=60`)

---

## 1. Zusammenfassung

Die Datenbeschaffung wurde von **passivem POST-Empfang** auf **aktives GET-Polling** via `NetworkClient` umgestellt. Die Umschaltung erfolgt über die `.env`-Variable `POKEY_SERVICE`.

| Aspekt | POST (Legacy) | GET (Neu) |
|--------|---------------|-----------|
| Datenfluss | Geräte pushen → App empfängt | App pollt → Geräte antworten |
| Kontrolle | Kein Einfluss auf Timing | `FETCH_INTERVAL` aus `.env` |
| Ausfallschutz | Nur Zähler-Reset im Store | Dreifach: S0Sensor + DB-Batch + NetworkClient |
| Persistenz | Nur JSON (`sensor_state.json`) | Dual: JSON + SQLite mit Cross-Check |
| Kollisionsschutz | — | POST-Router wird im GET-Modus **deaktiviert** |

---

## 2. Neue Dateien

| Datei | Beschreibung |
|-------|--------------|
| `app/infrastructure/network_client.py` | HTTP GET mit urllib3, Retry (3x), Timeout (2.5s/3s) |
| `app/domain/s0_sensor.py` | S0Sensor mit Spike-Schutz, Moving Average, Energieklasse |
| `app/domain/pokey_device.py` | PoKeys-Interface (ID, IP, Online/Offline) |
| `app/services/state/storage_handler.py` | Atomares JSON-Speichern (tempfile + os.replace) |
| `app/services/pokeys_manager.py` | Zentrale Steuerung + Polling-Thread |

## 3. Geänderte Dateien

| Datei | Änderung |
|-------|----------|
| `app/main.py` | Modus-Weiche GET/POST, POST-Router deaktiviert im GET-Modus |
| `app/api/dashboard2.py` | Live-Sensors + Verify dual-fähig (GET/POST) |
| `app/services/mqtt_publisher.py` | Dual-fähig: PoKeysManager oder SensorStore |
| `app/.env` | `POKEY_SERVICE=GET`, `FETCH_INTERVAL=60`, `MAPPING_ENABLED=true` |
| `requirements.txt` | `urllib3==2.4.0` hinzugefügt |

---

## 4. Kollisionsschutz: POST deaktiviert im GET-Modus

```python
# app/main.py — Router-Registrierung
if settings.POKEY_SERVICE.upper() != "GET":
    app.include_router(parsdecoder_router)
else:
    logger.info("Router: parsdecoder (POST) DEAKTIVIERT (GET-Modus aktiv).")
```

Im GET-Modus ist der POST-Endpoint `/` (parsdecoder) **nicht erreichbar**. Damit ist eine Doppelbuchung ausgeschlossen.

---

## 5. Datenbank-Integration

### Bestehende `Database`-Klasse wird genutzt

Der `PoKeysManager` nutzt die bestehende `Database`-Singleton-Klasse (`app/infrastructure/database/dbconnect.py`):

```python
# pokeys_manager.py
from app.infrastructure.database.dbconnect import Database

conn = Database._instance.get_conn(year=year)
conn.executemany("""
    INSERT INTO hourly_values (sensor_id, hour, consumption, total)
    VALUES (?, ?, ?, ?)
    ON CONFLICT(sensor_id, hour) DO UPDATE SET
        consumption = excluded.consumption,
        total = excluded.total
""", sql_rows)
```

### Tabellen-Sicherstellung

Beim Start wird `hourly_values` in der Lifespan erstellt (wie bisher). Der Manager prüft zusätzlich bei jedem Batch-Write, ob die Tabelle existiert (für neue Jahres-DBs).

### Jahres-Datenbanken

Wie bisher: `sensors_2026.db`, `sensors_2027.db` etc. — automatisch über `Database._instance.get_conn(year=...)`.

---

## 6. Schutzmaßnahmen (100% Appausfall-Schutz)

### Dreifacher Spike-Schutz

| Schicht | Mechanismus | Schwelle |
|---------|-------------|----------|
| S0Sensor.update() | Zähler-Reset (new < total) | Sofort |
| S0Sensor.update() | Spike-Rate | max 2 kWh/s |
| DB-Batch-Write | Absurde Spitze | max 50 kWh/h |

### Persistenz-Schutz

| Schicht | Mechanismus |
|---------|-------------|
| JSON (StorageHandler) | Atomares Schreiben via `tempfile` + `os.replace()` |
| SQLite | WAL-Modus + `ON CONFLICT DO UPDATE` |
| Cross-Check beim Start | JSON vs. SQLite → bester Wert gewinnt |

### Netzwerk-Schutz

- 3 Retries mit exponentiellem Backoff (0.5s)
- Connect-Timeout: 2.5s, Read-Timeout: 3.0s
- Bei Fehler: Device offline setzen, **App läuft weiter**
- Polling-Thread: `try/except` um gesamten Update-Zyklus

### Thread-Sicherheit

- Polling-Thread: `threading.Event` für sauberes Shutdown
- StorageHandler: Atomares Schreiben (single-writer)
- SQLite: WAL-Modus (paralleles Lesen möglich)
- `daemon=True`: Thread stirbt mit der App

---

## 7. Konfiguration (alles aus app_config)

Keine hardcodierten Werte. Alles kommt aus `settings`:

| Setting | Quelle | Verwendung |
|---------|--------|------------|
| `POKEY_SERVICE` | `.env` | Modus-Weiche GET/POST |
| `FETCH_INTERVAL` | `.env` | Polling-Intervall (60s Test, 300s Prod) |
| `POKEYS_DEVICE{n}_IP` | `.env` | Device-IPs |
| `POKEYS_DEVICE{n}_SENSORS` | `.env` | Sensor-Ranges |
| `POKEYS_DEVICE{n}_PINS` | `.env` | Pin-Mapping |
| `STROMPREISE` | `.env` | Kostenberechnung |
| `CO2_WERT` | `.env` | CO₂-Berechnung |
| `LIMIT_CLASS_A..F` | `.env` | Energieklassen |
| `DATA_DIR` | `.env` | Pfad für `pokeys_state.json` |
| `mapping_file` | `.env` (MAPPING_FILE) | Pfad zu `house.yaml` |

---

## 8. Dashboard-Erweiterung (Live-Sensors API)

Der Endpoint `GET /api/dashboard2/live/sensors` liefert im GET-Modus erweiterte Daten:

```json
{
  "id": "S32",
  "name": "Büro Rechner",
  "room": "Büro",
  "area": "Kellergeschoss",
  "watt": 199,
  "kosten": 0.024,
  "co2": 39.52,
  "prognose_tag": 1.15,
  "prognose_jahr": 420.47,
  "energieklasse": "G",
  "model": "eacWSZ-50A",
  "devices": ["rechner"],
  "status": "OK",
  "online": true
}
```

---

## 9. Rollback-Plan (optional)

```bash
# In app/.env:
POKEY_SERVICE=POST
FETCH_INTERVAL=300

# Container neu starten → alte POST-Logik greift sofort
```

Alle POST-Module bleiben im Code erhalten und funktionsfähig.

---

## 10. Testphase

- `FETCH_INTERVAL=60` (jede Minute)
- Prüfen: `GET /api/dashboard2/live/sensors` → Sensordaten mit Watt, Kosten, Status
- Prüfen: `GET /api/dashboard2/verify` → DB-Werte vs. Live-Werte
- Prüfen: MQTT Topics `smartmeters/sensors/S01` etc.
- Nach erfolgreicher Testphase: `FETCH_INTERVAL=300` für Produktion

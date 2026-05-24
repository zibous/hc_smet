# Refactoring: Vereinfachung der Datenverarbeitung (v3)

## Ziel

Die aktuelle Architektur hat zwei getrennte State-Systeme (`SensorStore` + `EnergyAggregator`),
die unabhängig voneinander Deltas berechnen. Das führt zu Sprüngen beim Übergang
Import → Live-Betrieb. Die neue Architektur eliminiert diese Fehlerquelle durch
ein einziges, zentrales State-System.

---

## Ablauf NEU

```
       [📡 PoKeys-Gerät (IF64/IF65)]
                     │
                     │  HTTP POST: "data=S01=948.50;S02=2044.36;..."
                     ▼
 ┌────────────────────────────────────────────────────────┐
 │ 1. EINGANG: app/api/parsdecoder.py                     │
 ├────────────────────────────────────────────────────────┤
 │ • Liest User-Agent Header (Device-Name)                │
 │ • Extrahiert Body-String                               │
 │ • Erzeugt SensorService                                │
 └───────────────────┬────────────────────────────────────┘
                     │
                     ▼
 ┌────────────────────────────────────────────────────────┐
 │ 2. SERVICE: app/services/sensor_service.py             │
 ├────────────────────────────────────────────────────────┤
 │ • Ruft Parser auf → Dict {"S01": 948.50, ...}          │
 │ • Validiert Werte (Pydantic)                           │
 │ • Übergibt an SensorStore.update()                     │
 └───────────────────┬────────────────────────────────────┘
                     │
                     ▼
 ┌────────────────────────────────────────────────────────┐
 │ 3. STORE: app/services/state/sensor_store.py           │
 ├────────────────────────────────────────────────────────┤
 │                                                        │
 │  Für jeden Sensor:                                     │
 │                                                        │
 │  ┌─ Kein vorheriger Wert? (Erststart/Import)           │
 │  │   → delta = 0, nur current speichern                │
 │  │   → NICHTS in DB schreiben                          │
 │  │                                                     │
 │  ├─ current < last? (Zähler-Reset)                     │
 │  │   → delta = 0, current als neuen Basiswert setzen   │
 │  │   → NICHTS in DB schreiben                          │
 │  │                                                     │
 │  └─ Normaler Folgewert                                 │
 │      → delta = round(current - last, 6)                │
 │      → Zeitlücke prüfen:                               │
 │        ├─ <= 1h: delta in aktuelle Stunde buchen       │
 │        └─ > 1h: delta gleichmäßig auf fehlende         │
 │                  Stunden verteilen                      │
 │      → hourly_values UPDATE (addiert delta)            │
 │                                                        │
 │  RAM-State aktualisieren + sensor_state.json sichern   │
 │                                                        │
 └───────────────────┬────────────────────────────────────┘
                     │
                     ▼
 ┌────────────────────────────────────────────────────────┐
 │ 4. DATENBANK: data/sensors_YYYY.db                     │
 ├────────────────────────────────────────────────────────┤
 │ • Tabelle: hourly_values (sensor_id, hour, consumption)│
 │ • SQLite WAL-Modus, thread-safe                        │
 │ • Keine sensor_state Tabelle mehr nötig                │
 └────────────────────────────────────────────────────────┘
```

---

## Regeln der Delta-Berechnung

| Situation | Aktion |
|-----------|--------|
| Erster Wert (kein `last` bekannt) | `delta = 0`, nur speichern |
| `current < last` (Zähler-Reset) | `delta = 0`, neuer Basiswert |
| `current == last` | `delta = 0`, nichts buchen |
| `current > last`, Zeitdiff ≤ 1h | `delta` in aktuelle Stunde addieren |
| `current > last`, Zeitdiff > 1h | `delta` gleichmäßig auf fehlende Stunden verteilen |

**Wichtig:** Es werden NIEMALS die absoluten Totalwerte (z.B. 23408.86) in
`hourly_values` geschrieben — immer nur das kleine Delta (z.B. 0.03).

---

## Sonderfall: Längerer Ausfall

Wenn zwischen zwei Werten mehr als 1 Stunde liegt (App war aus, Netzwerk-Problem):

- Das aufgelaufene Delta wird **verworfen** (nicht gebucht)
- Der aktuelle Zählerstand wird als neuer Basiswert gespeichert
- Ab dem nächsten Wert (30s später) läuft alles normal weiter

**Begründung:** Die fehlenden Stunden sind entweder bereits vom Import abgedeckt,
oder der Verbrauch ist nicht zuverlässig rekonstruierbar. Nachträgliches Verteilen
erzeugt Doppelbuchungen wenn Import-Daten vorhanden sind.

**Datenverlust:** Maximal der Verbrauch einer Stunde geht verloren. Das ist
akzeptabel — besser als falsche Sprünge im Dashboard.

---

## Sonderfall: Import → Live-Übergang

```
1. App stoppen (make down)
2. Neue DB vom Server holen:
   scripts/import_from_server.sh 2026
   → Ergebnis: scripts/data/sensors_2026.db
3. DB in den App-Datenordner kopieren:
   cp scripts/data/sensors_2026.db data/sensors_2026.db
4. sensor_state.json löschen:
   rm -f data/sensor_state.json
5. App starten (make up)

Beim ersten POST:
→ SensorStore hat keinen vorherigen Wert (JSON war leer)
→ delta = 0, nur current speichern
→ NICHTS in hourly_values geschrieben
→ Import-Stunde bleibt unberührt

Beim zweiten POST (30s später):
→ delta = current - last (winzig, z.B. 0.005)
→ In aktuelle Stunde buchen
→ Kein Sprung, kein Überlapp mit Import-Daten
```

**Warum das funktioniert:** Die Import-DB (`scripts/data/sensors_2026.db`) enthält
nur `hourly_values` — keine `sensor_state`-Tabelle, kein JSON. Beim Start ist der
SensorStore komplett leer. Der erste Live-Wert wird als Kalibrierung behandelt
(delta=0). Erst ab dem zweiten Wert werden echte Deltas berechnet und gebucht.
Da das Delta nur die Differenz der letzten 30 Sekunden ist, gibt es keinen Sprung.

---

## Dateien: Was ändert sich?

### Entfällt komplett

| Datei | Grund |
|-------|-------|
| `app/services/energy_aggregator.py` | Logik wandert in SensorStore |
| DB-Tabelle `sensor_state` | State lebt nur noch in JSON |

### Wird geändert

| Datei | Änderung |
|-------|----------|
| `app/services/state/sensor_store.py` | Erweitert: schreibt direkt in `hourly_values` |
| `app/services/sensor_service.py` | Vereinfacht: kein Aggregator-Aufruf mehr |
| `app/main.py` | Lifespan: kein EnergyAggregator() mehr, nur DB-Init |
| `scripts/getpokey_data.py` | Kein `DROP TABLE sensor_state` mehr nötig |

### Bleibt unverändert

| Datei | Grund |
|-------|-------|
| `app/api/parsdecoder.py` | Ruft weiterhin SensorService auf |
| `app/infrastructure/parsers/parsePostdata.py` | Parser-Logik unverändert |
| `app/infrastructure/database/dbconnect.py` | DB-Singleton bleibt |
| `app/infrastructure/database/energy_repository.py` | Liest weiterhin hourly_values |
| `app/api/dashboard.py` + Builder | Dashboard liest nur, schreibt nicht |
| `app/api/dashboard2.py` | Live-Dashboard unverändert |
| `frontend/` | Komplett unverändert |
| `analytics/` | Liest nur hourly_values, unverändert |

---

## Neues DB-Schema

```sql
-- Einzige Tabelle in sensors_YYYY.db
CREATE TABLE IF NOT EXISTS hourly_values (
    sensor_id TEXT NOT NULL,
    hour INTEGER NOT NULL,
    consumption REAL NOT NULL,
    total REAL,
    PRIMARY KEY (sensor_id, hour)
);
CREATE INDEX IF NOT EXISTS idx_hour ON hourly_values(hour);
```

- `consumption`: Das aufaddierte Delta für diese Stunde (kWh)
- `total`: Der letzte bekannte Zählerstand (NULL bei Import, befüllt bei Live)

Keine `sensor_state`-Tabelle mehr. Der State lebt ausschließlich in:
- **RAM:** `SensorStore.data` (Dict mit current, last, delta, timestamp)
- **Disk:** `data/sensor_state.json` (Persistenz über Neustarts)
- **Fallback:** `hourly_values.total` (Recovery wenn JSON fehlt/korrupt)

---

## SensorStore.update() — Neue Logik (Pseudocode)

```python
def update(self, new_data: dict):
    now_ts = int(time.time())
    current_hour = (now_ts // 3600) * 3600

    for sensor_id, raw_value in new_data.items():
        current = round(float(raw_value), 6)
        old = self.data.get(sensor_id)

        # --- KALIBRIERUNG ---
        if not old or sensor_id not in self._calibrated_sensors:
            delta = 0.0
            self._calibrated_sensors.add(sensor_id)

        # --- ZÄHLER-RESET ---
        elif current < old.current:
            delta = 0.0

        # --- NORMALER WERT ---
        else:
            delta = round(current - old.current, 6)

        # --- RAM AKTUALISIEREN ---
        self.data[sensor_id] = SensorStateEntry(
            current=current,
            last=old.current if old else current,
            delta=delta,
            timestamp=now_ts
        )

        # --- IN DB SCHREIBEN (nur wenn delta > 0) ---
        if delta > 0 and old:
            time_diff = now_ts - old.timestamp

            if time_diff <= 3600:
                # Alles in die aktuelle Stunde
                self._db_add_hour(sensor_id, current_hour, delta)
            else:
                # Gleichmäßig auf fehlende Stunden verteilen
                hours_missed = time_diff // 3600
                per_hour = round(delta / hours_missed, 6)
                start_hour = (old.timestamp // 3600) * 3600

                for i in range(hours_missed):
                    h = start_hour + (i * 3600)
                    self._db_add_hour(sensor_id, h, per_hour)

    self._save()  # JSON persistieren
```

---

## Migrationsschritte

1. `sensor_store.py` erweitern (DB-Zugriff hinzufügen)
2. `sensor_service.py` vereinfachen (Aggregator-Code entfernen)
3. `main.py` Lifespan anpassen (nur DB-Init, kein Aggregator)
4. `energy_aggregator.py` löschen
5. Testen: Import → Start → Prüfen ob Werte korrekt sind
6. `getpokey_data.py` aufräumen (kein `DROP TABLE sensor_state`)

---

## Vorteile

- **Ein** State-System statt zwei → keine Inkonsistenzen
- Import-Übergang ist trivial (erster Wert = Kalibrierung, fertig)
- Kein Timestamp-Marker, kein `end_of_last_hour`, keine Race-Conditions
- Weniger Code (~150 Zeilen weniger)
- Gleichmäßige Verteilung bei Ausfällen eingebaut
- Testbar: SensorStore kann isoliert mit Mock-DB getestet werden

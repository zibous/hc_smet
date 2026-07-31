---
title: "⚡ 50 Stromzähler im Haus – Granulare Verbrauchsmessung mit S0-Sensoren"
date: 2026-06-24T20:00:00
description: "50 S0-Impulszähler, zwei PoKeys57E Ethernet-Controller und 13 Jahre Messhistorie – so wird jede Steckdose im Haus zum transparenten Datenpunkt."
type: "post"
draft: false
image: "posts/smarthome-smartmeters/smartmeters.png"
author: "Peter Siebler"
snap_gallery: true
gallery: true
categories:
  - "Smarthome"
tags: ["docker", "python", "fastapi",  "dashboard", "mqtt", "homeassistant"]
---

[![Github Project](https://img.shields.io/badge/Project-GitHub-yellow.svg)](https://github.com/zibous/hc_smet)
[![Support author](https://img.shields.io/badge/buy%20me%20a%20coffee-orange.svg)](https://www.buymeacoff.ee/zibous)
[![License](https://img.shields.io/badge/license-Open%20Source-green.svg)](https://opensource.org)
![Python](https://img.shields.io/badge/Python-3.12-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688.svg)
[![Support author](https://img.shields.io/badge/buy%20me%20a%20coffee-orange.svg)](https://www.buymeacoff.ee/zibous)


## Jeder Raum, jedes Gerät – granulare Strommessung seit 2013

Der Standard-Stromzähler im Keller zeigt den Gesamtverbrauch. Aber **wer** im Haus verbraucht **wie viel**? Die Küche? Das Home-Office? Die Waschmaschine? Mit **hc_smet** wird jeder einzelne Stromkreis sichtbar: 50 S0-Impulszähler verteilt über 5 Geschosse, angebunden über zwei PoKeys57E Ethernet-Controller, liefern alle 5 Minuten Messdaten – und das seit 13 Jahren.

<!--more-->

## Das Hardware-Setup: 50 Zähler im Zählerschrank

### S0-Impulszähler

Im Zählerschrank des Kellers sitzen **50 Hutschienen-Stromzähler** vom Typ eacWSZ-50A (bis 50A, 1000 Impulse/kWh) und eacDSZ-63A (bis 63A, 800 Impulse/kWh). Jeder Zähler überwacht einen einzelnen Stromkreis – von der Tiefkühltruhe über den Kühlschrank bis zum Boiler.

### PoKeys57E Ethernet-Controller

Die S0-Impulse werden von zwei **PoKeys57E** Controllern erfasst (Hersteller: PoLabs, Slovenien). Diese Ethernet-I/O-Controller haben je 55 digitale I/O-Pins und eine eingebaute HTTP-API:

| Controller | IP | Sensoren | Funktion |
|------------|-----|----------|----------|
| **poKey64** | 10.1.1.64 | S01–S25 | Kellergeschoss, Wohngeschoss |
| **poKey65** | 10.1.1.65 | S26–S50 | Obergeschoss, Dachgeschoss, Außen |

Jeder Controller liefert über `GET /sensorList.json` die aktuellen Zählerstände aller angeschlossenen Sensoren als JSON.

---

## 🏗️ Architektur & Datenfluss

{{< mermaid >}}
flowchart TD
    Main["main.py (Lifespan)<br>DB init · PoKeys · MQTT · Webhooks"] --> Sensor["Sensor-Datenerfassung<br>POST: PoKeys → App<br>GET: App pollt PoKeys (5min)"]
    Main --> API["FastAPI Server :8096<br>/api/sensors · /api/room · /api/area<br>/api/home · /api/dashboard · /api/kpidata"]
    Sensor --> Service["SensorService<br>Normalisierung · Reset-Erkennung · Delta"]
    Service --> DB["SQLite DB (pro Jahr)<br>current_values · hourly_values"]
    DB --> Calc["Calculator (on-demand)<br>Tag/Woche/Monat/Jahr + Vergleich"]
    Main --> Topo["HouseTopology (house.yaml)<br>50 Sensoren → 20 Räume → 6 Bereiche"]
    Main --> MQTT["MQTT Publisher (5 Min)<br>smartmeters/sensors · rooms · areas · home"]
{{< /mermaid >}}

Die App unterstützt zwei Betriebsmodi:
- **POST-Modus**: Die PoKeys-Controller senden aktiv Daten an die App (Push)
- **GET-Modus**: Die App pollt die Controller alle 5 Minuten (Pull)

---

## 🏠 Die Haus-Topologie – Vom Sensor zum Gesamtverbrauch

Das Besondere an hc_smet ist die **hierarchische Aggregation**. Jeder Sensor gehört zu einem Raum, jeder Raum zu einem Bereich, alle Bereiche zum Haus:

```text
HOME (Haus-Gesamt: 50 Sensoren)
├── EG – Kellergeschoss
│   ├── Büro (Rechner)
│   ├── Wirtschaftsraum (Heizung, Boiler, Waschmaschine, Trockner)
│   ├── Vorratsraum (Tiefkühltruhe)
│   └── Zählerschrank (Technik, Netzteil)
├── WG – Wohngeschoss
│   ├── Küche (Herd, Kühlschrank, Spülmaschine, Licht, Geräte)
│   ├── Wohnzimmer (Media, Verbraucher)
│   └── Gäste WC
├── OG – Obergeschoss
│   ├── Bad (Dampfdusche, Licht)
│   ├── Schlafzimmer
│   └── Kinderzimmer (2×)
├── DG – Dachgeschoss
│   └── Fitnessraum (Media, Strom, Wechselrichter)
└── OS – Außenbereich
    └── Garage
```

Abfragen funktionieren auf jeder Ebene:
- `/api/sensor/S13` → Kühlschrank einzeln
- `/api/room/WG_R03` → Küche gesamt (7 Sensoren summiert)
- `/api/area/WG` → Wohngeschoss gesamt
- `/api/home` → Gesamthaus

---

## 📊 Periodenberechnung

Für jeden Sensor und jede Aggregationsebene werden automatisch berechnet:

| Periode | Berechnung | Vergleich |
|---------|-----------|-----------|
| **Tag** | Verbrauch seit Mitternacht | vs. Vortag |
| **Woche** | Verbrauch seit Montag 0:00 | vs. Vorwoche |
| **Monat** | Verbrauch seit 1. des Monats | vs. Vormonat |
| **Jahr** | Verbrauch seit 1. Januar | vs. Vorjahr |

```json
{
  "id": "S13",
  "name": "Kühlschrank",
  "room": "Küche",
  "area": "Wohngeschoss",
  "total": 2847.3,
  "current": 0.04,
  "day": 0.72,
  "yesterday": 0.68,
  "week": 4.9,
  "lastweek": 5.1,
  "month": 21.4,
  "lastmonth": 20.8,
  "year": 127.6
}
```

---

## 🧮 Sensor-Reset-Erkennung

Ein häufiges Problem bei Impulszählern: Nach einem Stromausfall oder Firmware-Update wird der Zählerstand zurückgesetzt. Die App erkennt das automatisch:

```
Wenn total < last_total → Reset erkannt
  → current = total (statt negativ)
  → Nächster Wert wird wieder normal berechnet
```

Kein manuelles Eingreifen nötig – die Zeitreihe bleibt konsistent.

---

## 📈 13 Jahre Messhistorie

Die Daten reichen bis 2013 zurück – eine gute Langzeit-Datenbasis:

| Metrik | Wert |
|--------|------|
| **Aktive Sensoren** | ~35 (von 50) |
| **Messungen pro Tag** | 14.400 |
| **Stundenwerte pro Jahr** | 438.000 |
| **Gesamtarchiv** | ~5,7 Millionen Datenpunkte |
| **DB-Größe pro Jahr** | ~50 MB |

## Langzeit-Datenbasis: 13 Jahre Stromsensoren-Daten

Mit einer Datenbasis aus stolzen 13 Jahren kontinuierlicher Strommessung lässt sich einiges optimieren
und tiefgehend analysieren. Diese wertvollen Langzeitdaten bieten die perfekte Grundlage,
um den eigenen Stromverbrauch nicht nur besser zu verstehen, sondern ihn auch gezielt und
sinnvoll zu steuern.

Wer so tief in seine Daten eintauchen kann, deckt versteckte Standby-Fresser
auf und findet echtes Einsparungspotenzial, das sich bares Geld spart.

Jedes Jahr hat seine eigene SQLite-Datei (`sensors_YYYY.db`). Das verhindert Datenbank-Aufblähung und
macht Backups einfach.

### Jahresvergleich

Das Dashboard bietet eine **Chart.js Visualisierung** aller Jahre:
- Balkendiagramm mit Jahresgesamtverbrauch
- Prozentuale Veränderung Jahr-über-Jahr
- Identifikation von Ausreißern (neue Geräte, Verhaltensänderung)

---

## 🖥️ Web Dashboard

### Übersichts-Dashboard
- KPI-Cards: Gesamtverbrauch heute/Monat/Jahr
- Top-Verbraucher (Sensor-Ranking nach kWh)
- Bereichs-Übersicht (Tortengrafik nach Geschoss)
- Sensor-Status (online/offline)

### Live Dashboard (`/live`)
- Echtzeit-Anzeige aller Sensoren
- Aktuelle Leistung und Tagesverbrauch
- Farbcodierung nach Effizienzklasse (A–F)

### Zeitreihen-Dashboard
- Stündliche Auflösung
- Frei wählbarer Zeitraum
- Vergleich mit Vorperiode
- Drill-Down: Haus → Bereich → Raum → Sensor

---

## 🔗 Home Assistant Integration

### MQTT Auto-Discovery

Bei aktiviertem MQTT registrieren sich alle 50 Sensoren + Aggregationen automatisch in Home Assistant:

```
smartmeters/sensors/S01 → sensor.smartmeters_wirtschaftsraum_licht
smartmeters/sensors/S13 → sensor.smartmeters_kuehlschrank
smartmeters/rooms/WG_R03 → sensor.smartmeters_kueche
smartmeters/areas/WG → sensor.smartmeters_wohngeschoss
smartmeters/home → sensor.smartmeters_haus_gesamt
```

### Webhooks

| Event | Auslöser | Daten |
|-------|----------|-------|
| **heartbeat** | Alle 5 Min | Haus-Gesamtverbrauch + Sensor-Count |
| **daily_summary** | 0:00 | Tagesverbrauch pro Bereich |
| **monthly_summary** | 1. des Monats | Monatsverbrauch + Kosten |

---

## 💰 Kostenberechnung

Aus `STROMPREISE={"2026": 0.24}` berechnet die App für jeden Sensor:

```
Kosten = Verbrauch (kWh) × Strompreis (€/kWh)
```

Im Dashboard sieht man sofort: Der Boiler kostet 45 €/Monat, der Kühlschrank 5 €/Monat, das Home-Office 12 €/Monat.

---

## ⚙️ Installation & Konfiguration

### Docker (empfohlen)

```bash
git clone <repo-url> hc_smet
cd hc_smet
cp .env_example .env
nano .env                    # PoKeys IPs + MQTT setzen
make build && make up
# → Dashboard: http://localhost:5045
```

### Wichtige Umgebungsvariablen

| Variable | Default | Beschreibung |
|----------|---------|--------------|
| `POKEY_SERVICE` | `POST` | Betriebsmodus (POST/GET) |
| `POKEYS_DEVICE1_IP` | `10.1.1.64` | IP PoKey64 |
| `POKEYS_DEVICE2_IP` | `10.1.1.65` | IP PoKey65 |
| `FETCH_INTERVAL` | `300` | Polling-Intervall in Sekunden |
| `MQTT_ENABLED` | `false` | MQTT aktivieren |
| `MQTT_HOST` | `localhost` | MQTT Broker |
| `DB_ENABLED` | `false` | SQLite persistieren |
| `MAPPING_ENABLED` | `false` | Haus-Topologie aktivieren |
| `STROMPREISE` | `{"2026": 0.24}` | Strompreis (€/kWh) pro Jahr |

---

## 🛠️ Technologie-Stack

| Komponente | Technologie |
|------------|-------------|
| **Backend** | Python 3.12, FastAPI, Pydantic Settings |
| **Datenbank** | SQLite (Jahr-basiert, Thread-safe) |
| **Frontend** | Jinja2, ES-Module, Chart.js |
| **Controller** | PoKeys57E (HTTP JSON API) |
| **Sensoren** | 50× S0-Impulszähler (eacWSZ/eacDSZ) |
| **Integration** | MQTT Discovery, HA Webhooks |
| **Deployment** | Docker Compose, Make-Workflow |

---

## 💡 Erkenntnisse aus 13 Jahren Messung

Einige interessante Muster aus über einer Dekade Stromverbrauchsdaten:

- **Top 3 Verbraucher**: Boiler (S34), Herd (S35), Waschmaschine/Trockner (S36) – zusammen ~40% des Gesamtverbrauchs
- **Kühlschrank-Degradation**: S13 zeigt über die Jahre einen langsam steigenden Verbrauch – Hinweis auf nachlassende Effizienz
- **Home-Office-Effekt 2020**: Der Büro-Sensor (S32) verdoppelte sich während COVID von 1,2 kWh/Tag auf 2,4 kWh/Tag
- **PV-Eigenverbrauch**: Der Wechselrichter-Sensor (S23) zeigt die PV-Erzeugung – korreliert perfekt mit den Einspeise-Daten
- **Standby-Verbrauch**: Nachts (0–6 Uhr) zieht das Haus konstant ~300W Grundlast – verteilt auf Netzteile, Router, Kühlgeräte
- **Saisonalität**: Winterverbrauch (+35%) durch Beleuchtung, Heizungspumpe und kürzere PV-Erträge

<hr style="margin-bottom: 4rem">

### Dashboard & Jahresvergleich
{{< gallery >}}
  {{< image-dir >}}
{{< /gallery >}}

<hr style="margin-bottom: 4rem">

{{< notice tip >}}
  &raquo; **Effizienzklassen**: Die App kategorisiert Sensoren in Klassen A–F basierend auf kWh/Tag. Ab Klasse D (>300 Wh/Tag) lohnt sich ein genauer Blick auf den Verbraucher.<br>
  &raquo; **PoKeys-Firmware**: Die Controller laufen stabil mit der Original-Firmware von 2017. Kein Update nötig – never change a running system.<br>
  &raquo; **Sensor-Reset**: Nach einem Stromausfall erkennt die App den Zähler-Reset automatisch. Kein manuelles Nachpflegen nötig.<br>
  &raquo; **Jahres-DB archivieren**: Die alten `sensors_YYYY.db` Dateien sind ideal für Langzeit-Analysen – regelmäßig sichern!<br>
{{< /notice >}}

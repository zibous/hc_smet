
# 📘 PoKeys Energy Monitoring

Ein modulares Python‑System zur Erfassung, Verarbeitung und Visualisierung
von Energieverbrauchsdaten über PoKeys‑Interfaces (S0‑Zähler).
Das System unterstützt mehrere PoKeys‑Geräte, automatische Sensor‑Zuordnung,
Pin‑Mapping, Online/Offline‑Erkennung und persistente Speicherung.

## 🚀 Features

- Automatische Zuordnung von 50 Sensoren zu zwei PoKeys‑Interfaces
- Pin‑Mapping basierend auf PoKeys‑Pinreihenfolge
- Online/Offline‑Erkennung pro Interface und Sensor
- Persistente Speicherung aller Messwerte (JSON)
- Berechnung von:
    - Watt
    - kWh (Differenzmessung)
    - total_kWh
- YAML‑basierte Haus‑ und Sensor‑Konfiguration
- Saubere, modulare Architektur

## Hardware

### Interface
    - 2x PoKeys57E
    - Firmware v4.5.13

### Stromzähler S0
 - Kanal 1: eacWSZ-50A (Wechselstromzähler)
   Auflösung: 1000 Impulse / kWh
   Bedeutung: 1 Impuls = exakt 1 Wattstunde (Wh) oder 0,001 kWh.
   Berechnung: kWh = Gesamt-Impulse / 1000

 - Kanal 2: eacDSZ-63A (Drehstromzähler)
   Auflösung: 800 Impulse / kWh
   Bedeutung: 1 Impuls = 1,25 Wattstunden (Wh) oder 0,00125 kWh.
   Berechnung: kWh = Gesamt-Impulse / 800

### Sesnorlist data
Struktur und Auslesen der sensorList.json
An den Hardware-Pins sind digitale Zähler eingerichtet und daher liefert die http://<IP-ADRESSE>/sensorList.json
ein strukturiertes Array.
Ein typischer Eintrag sieht strukturell so aus:

```json
    "sensors":[
    {"ID":"S01","Disp":0,"P1":0,"P2":0,"Val":955.86,"Min":0,"Max":0,"U":"kWh"},
    {"ID":"S02","Disp":0,"P1":0,"P2":0,"Val":2060.41,"Min":0,"Max":0,"U":"kWh"},
    {"ID":"S03","Disp":0,"P1":0,"P2":0,"Val":53.16,"Min":0,"Max":0,"U":"kWh"},
    {"ID":"S04","Disp":0,"P1":0,"P2":0,"Val":1363.85,"Min":0,"Max":0,"U":"kWh"},
    {"ID":"S05","Disp":0,"P1":0,"P2":0,"Val":3584.41,"Min":0,"Max":0,"U":"kWh"},
    {"ID":"S06","Disp":0,"P1":0,"P2":0,"Val":302.90,"Min":0,"Max":0,"U":"kWh"},
    {"ID":"S07","Disp":0,"P1":0,"P2":0,"Val":1959.48,"Min":0,"Max":0,"U":"kWh"},
    {"ID":"S08","Disp":0,"P1":0,"P2":0,"Val":7285.78,"Min":0,"Max":0,"U":"kWh"},
    {"ID":"S09","Disp":0,"P1":0,"P2":0,"Val":290.74,"Min":0,"Max":0,"U":"kWh"},
    {"ID":"S10","Disp":0,"P1":0,"P2":0,"Val":1780.88,"Min":0,"Max":0,"U":"kWh"},
    {"ID":"S11","Disp":0,"P1":0,"P2":0,"Val":5940.40,"Min":0,"Max":0,"U":"kWh"},
    {"ID":"S12","Disp":0,"P1":0,"P2":0,"Val":1345.18,"Min":0,"Max":0,"U":"kWh"},
    {"ID":"S13","Disp":0,"P1":0,"P2":0,"Val":3496.39,"Min":0,"Max":0,"U":"kWh"},
    {"ID":"S14","Disp":0,"P1":0,"P2":0,"Val":0.00,"Min":0,"Max":0,"U":"kWh"},
    {"ID":"S15","Disp":0,"P1":0,"P2":0,"Val":590.20,"Min":0,"Max":0,"U":"kWh"},
    {"ID":"S16","Disp":0,"P1":0,"P2":0,"Val":175.29,"Min":0,"Max":0,"U":"kWh"},
    {"ID":"S17","Disp":0,"P1":0,"P2":0,"Val":202.46,"Min":0,"Max":0,"U":"kWh"},
    {"ID":"S18","Disp":0,"P1":0,"P2":0,"Val":304.83,"Min":0,"Max":0,"U":"kWh"},
    {"ID":"S19","Disp":0,"P1":0,"P2":0,"Val":1358.27,"Min":0,"Max":0,"U":"kWh"},
    {"ID":"S20","Disp":0,"P1":0,"P2":0,"Val":0.00,"Min":0,"Max":0,"U":"kWh"},
    {"ID":"S21","Disp":0,"P1":0,"P2":0,"Val":0.00,"Min":0,"Max":0,"U":"kWh"},
    {"ID":"S22","Disp":0,"P1":0,"P2":0,"Val":0.00,"Min":0,"Max":0,"U":"kWh"},
    {"ID":"S23","Disp":0,"P1":0,"P2":0,"Val":0.00,"Min":0,"Max":0,"U":"kWh"},
    {"ID":"S24","Disp":0,"P1":0,"P2":0,"Val":0.00,"Min":0,"Max":0,"U":"kWh"},
    {"ID":"S25","Disp":0,"P1":0,"P2":0,"Val":0.00,"Min":0,"Max":0,"U":"kWh"}]}
```

### http://<Device IP>/devStat.xml

Bei älteren Firmware-Versionen (wie der v4.1.x) lief der interne 16-Bit- oder 32-Bit-Wert
der Zähler-Variablen in der XML-Struktur bei hohen Impulszahlen
regelmäßig über oder wurde im XML-Parser falsch formatiert.
In meinem Fall tritt dies ein und daher kann diese Variante nicht verwendet werden.

## 💡 Wichtiger Praxistipp zum Firmware-Zusammenhang

Falls  PoKeys57E unerwartet neu startet (z. B. durch einen Stromausfall),
wird der Zählerstand im RAM auf 0 zurückgesetzt.

Die neuere Firmware v4.5.13 verbessert hierbei die Stabilität des internen
EEPROM-Speichers erheblich, falls Sie die Funktion "Save counter to non-volatile memory" (Zählerstand netzausfallsicher speichern)
in der PoKeys-Konfiguration aktivieren.

Alternativ sollten Sie den fortlaufenden Zählerstand (Totalstapel) in Ihrer
Smart-Home-Software als "fortlaufenden Sensor" (Tarifzähler) definieren,
der mathematisch nur positive Änderungen aufaddiert.

## 🧠 Systemarchitektur

```bash
┌──────────────────────────────────────┐
│            SYSTEM START              │
└──────────────────────────────────────┘
                │
                ▼
      ┌──────────────────────┐
      │  YAML (house.yaml)   │
      │  Sensor-Definitionen │
      └──────────────────────┘
                │
                ▼
      ┌──────────────────────┐
      │ Sensor-Objekte bauen │
      │ (S01–S50)            │
      └──────────────────────┘
                │
                ▼
┌─────────────────────────────────┐
│   AUTOMATISCHE ZUORDNUNG        │
│   S01–S25 → Z1 (10.1.1.64)      │
│   S26–S50 → Z2 (10.1.1.65)      │
└─────────────────────────────────┘
                │
                ▼
      ┌──────────────────────┐
      │ Pin-Mapping laden    │
      │ pin_order[0..24]     │
      └──────────────────────┘
                │
                ▼
┌────────────────────────────────────────────┐
│   PIN-ZUORDNUNG                            │
│   Z1: S01→Pin0, S02→Pin1, ... S25→Pin48    │
│   Z2: S26→Pin0, S27→Pin1, ... S50→Pin48    │
└────────────────────────────────────────────┘
                │
                ▼
      ┌──────────────────────┐
      │ JSON laden (Storage) │
      │ alte Werte, kWh, ts  │
      └──────────────────────┘
                │
                ▼
      ┌──────────────────────┐
      │      UPDATE LOOP     │
      └──────────────────────┘
                │
                ▼
      ┌──────────────────────┐
      │  fetch(Z1.ip)        │
      │  fetch(Z2.ip)        │
      └──────────────────────┘
                │
                ▼
┌──────────────────────────────────────────────────────────────┐
│   ONLINE?                                                    │
│   ┌───────────────┬────────────────────────────────────────┐ │
│   │   JA          │   NEIN                                 │ │
│   ├───────────────┼────────────────────────────────────────┤ │
│   │ Werte lesen   │ Sensoren dieses Geräts offline setzen  │ │
│   │ JSON parsen   │ dev.online = False                     │ │
│   │ Sensor.update │                                        │ │
│   └───────────────┴────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
                │
                ▼
      ┌──────────────────────┐
      │ Werte speichern      │
      │ (StorageHandler)     │
      └──────────────────────┘
                │
                ▼
┌──────────────────────────────────────────────────────────────┐
│                     DATEN FÜR UI / API                       │
│   get_all_data() → {                                         │
│       "S01": { name, watt, kwh, total_kwh,                   │
│                pin, device_id, online, status }              │
│       ...                                                    │
│   }                                                          │
└──────────────────────────────────────────────────────────────┘
                │
                ▼
      ┌──────────────────────┐
      │ Anzeige / Konsole    │
      │ Web-UI / Logging     │
      └──────────────────────┘
```

## 🗂️ Modulübersicht

### manager.py

Zentrale Steuerung des Systems:

- lädt YAML‑Konfiguration
- erzeugt Sensor‑Objekte
- ordnet Sensoren automatisch PoKeys‑Interfaces zu
- führt Pin‑Mapping durch
- lädt/speichert Messwerte
- ruft Netzwerk‑Abfragen auf
- aktualisiert Sensorwerte
- liefert fertige Daten für UI/CLI

```python
    from manager import PoKeysManager
    m = PoKeysManager()
    m.update_sensors()
    print(m.get_all_data())
```

## pokeydevice.py

Repräsentiert ein physisches PoKeys‑Interface:

- ID (Z1/Z2)
- IP‑Adresse
- Sensorbereich (S01–S25 / S26–S50)
- Online/Offline‑Status
- Liste der zugeordneten Sensoren

### sensor.py

Repräsentiert einen einzelnen S0‑Sensor:

- Name, Raum, Modell
- Impulse pro kWh
- Pin, Interface‑ID
- Online‑Status
- Berechnung von Watt, kWh, total_kWh
- update() verarbeitet neue Messwerte

```log
    === S32 (Büro Rechner) ===
    name                : Büro Rechner
    impulse             : 1000
    faktor              : 0.1
    interface           : poKey65
    pin                 : 14
    model               : eacWSZ-50A
    room                : EG_R01
    devices             : ['rechner']
    total_kwh           : 2361.449
    prev_kwh            : 2361.448
    verbrauch_kwh       : 0.001
    watt                : 352
    last_ts             : 1779696242.0790763
    initialized         : True
    kosten              : 0.00024
    co2                 : 0.38
    kwh_pro_stunde      : 0.35229627400851177
    prognose_tag        : 2.03
    prognose_jahr       : 740.67
    sekunden_pro_impuls : 10.23
    online              : True
    last_online_ts      : 1779696242.079076
```


### network.py

Kommuniziert mit den PoKeys‑Geräten:

- HTTP‑GET auf /sensorList.json
- Timeout‑Handling
- JSON‑Parsing
- Rückgabe: { online: True/False, data: {...} }

### storage.py

Logik: Fällt der Wert in der sensorList.json plötzlich von z.B. 15000 auf 0 zurück,
erkennt die Software den Geräteneustart.


- Persistente Speicherung:
- speichert alle Sensorwerte in JSON
- lädt sie beim Start wieder
- verhindert Datenverlust bei Neustarts
- WICHTIG bei Device Neustart: Neuen Wert einfach auf den alten,
  im der json (peristant storage) gesicherten Stand oben drauf.

### house.yaml - sensors

Konfigurationsdatei:

- Sensor‑IDs
- Namen
- Räume
- logische Verbrauchergruppen
- Impulse
- Modell


## Testcase

```python
import time
from manager import PoKeysManager

def main():

    manager = PoKeysManager()
    print("Starte Standalone-Testlauf mit Differenz-Verbrauchsrechnung...")
    print("-" * 80)
    print("Initialisiere Basis-Zählerstände (Bitte kurz warten)...")
    manager.update_sensors()

    time.sleep(10)

    while True:

        manager.update_sensors()
        print(f"\nMessdaten :[{manager.letztes_update}]\n")
        daten = manager.get_all_data()

        # Tabellenkopf
        print(f"{'ID':<5} {'Name':<25} {'Status':<12} {'Total kWh':>12} {'Δ kWh':>10} {'Watt':>8} {'Faktor':>8}")
        print("-" * 90)
        for sensor, info in daten.items():
            if info['total_kwh'] > 0:
                print(
                    f"{sensor:<5} "
                    f"{info.get('name','-'):<25} "
                    f"{info.get('status'):<12} "
                    f"{info.get('total_kwh'):>12.3f} "
                    f"{info.get('kwh'):>10.3f} "
                    f"{info.get('watt'):>8} "
                    f"{info.get('faktor'):>8}"
                )

        time.sleep(60)

if __name__ == "__main__":
    main()

```

## 📊 Sensor‑Übersicht

```
| ID   | Name                      | Status | Total kWh | Δ kWh  | Watt | Faktor |
|------|---------------------------|--------|-----------|--------|------|--------|
| S01  | Licht                     | OK     | 95.584    | 0.001  | 59   | 0.1    |
| S02  | Heizung                   | OK     | 206.035   | 0.000  | 0    | 0.1    |
| S03  | Abwasserpumpe             | OK     | 5.316     | 0.000  | 0    | 0.1    |
| S04  | Gang / Vorratsraum        | OK     | 136.380   | 0.000  | 0    | 0.1    |
| S05  | Tiefkühltruhe             | OK     | 358.440   | 0.000  | 0    | 0.1    |
| S06  | Technik EG                | OK     | 30.289    | 0.000  | 0    | 0.1    |
| S07  | Gäste WC                  | OK     | 195.941   | 0.000  | 0    | 0.1    |
| S08  | Küchengeräte              | OK     | 728.538   | 0.002  | 119  | 0.1    |
| S09  | Licht & Steckdosen        | OK     | 29.074    | 0.000  | 0    | 0.1    |
| S10  | Wohnzimmer Verbraucher    | OK     | 178.083   | 0.000  | 0    | 0.1    |
| S11  | Wohnzimmer Media          | OK     | 594.029   | 0.000  | 0    | 0.1    |
| S12  | Küchenmöbel               | OK     | 134.517   | 0.000  | 0    | 0.1    |
| S13  | Kühlschrank               | OK     | 349.613   | 0.001  | 59   | 0.1    |
| S15  | Abwaschmaschine           | OK     | 59.020    | 0.000  | 0    | 0.1    |
| S35  | Herd                      | OK     | 282.577   | 0.000  | 0    | 0.125  |
| S16  | Licht & Steckdosen        | OK     | 17.529    | 0.000  | 0    | 0.1    |
| S17  | Kinderzimmer 2            | OK     | 20.246    | 0.000  | 0    | 0.1    |
| S19  | Kinderzimmer 1            | OK     | 135.822   | 0.001  | 59   | 0.1    |
| S29  | Garage                    | OK     | 87.306    | 0.000  | 0    | 0.1    |
| S30  | Zählerschrank Geräte      | OK     | 68.777    | 0.000  | 0    | 0.1    |
| S37  | Zählerschrank Netzteil    | OK     | 70.431    | 0.000  | 0    | 0.125  |
| S32  | Büro Rechner              | OK     | 2360.972  | 0.003  | 179  | 0.1    |
| S33  | Bad                       | OK     | 265.234   | 0.000  | 0    | 0.1    |
| S36  | Waschmaschine & Trockner  | OK     | 179.604   | 0.000  | 0    | 0.125  |
| S26  | Reserve                   | OK     | 283.649   | 0.000  | 0    | 0.1    |

```


## Schritt-für-Schritt-Anleitung für das Hardware-RecoveryStromversorgung trennen:

Ziehen Sie die Spannungsversorgung (5V DC) vom PoKeys57E ab.

Pins überbrücken:
- Suchen Sie den Pin 54 auf der Platine (dieser ist in der Regel am Rand der Anschlussleiste direkt mit "Reset" beschriftet).
- Verbinden Sie diesen Pin 54 mithilfe eines kleinen Drahts oder einer Jumper-Brücke mit einem GND-Pin (Masse).
- Ein passender GND-Pin befindet sich beispielsweise direkt in der Nähe zwischen den Pins 44 und 45.

PC vorbereiten:
- Schließen Sie das Board per LAN-Kabel direkt an Ihren PC an und stellen Sie sicher,
  dass Ihre PC-Netzwerkkarte auf eine feste IP-Adresse im Bereich 192.168.1.X eingestellt ist (z. B. 192.168.1.50).

Stromversorgung einschalten:
- Schalten Sie die 5V-Spannungsversorgung des PoKeys57E wieder ein, während die Brücke zwischen Pin 54 und GND noch gesteckt ist.
- Brücke entfernen: Nach etwa 2–3 Sekunden können Sie den Draht/die Brücke wieder entfernen.
- Das Board verbleibt nun für diesen Startvorgang im geschützten Recovery-Modus.Flashen:
  - Starten Sie die PoKeys-Konfigurationssoftware auf dem PC.
  - Das Board taucht nun in der Netzwerk-Geräteliste auf.
  - Klicken Sie auf das Gerät und wählen Sie den Punkt „Recovery“ (in manchen älteren deutschen Software-Versionen auch kurios als „Wieder“ übersetzt).
  - Die Software spielt die Firmware v4.8.2 nun ohne Blockaden neu auf.
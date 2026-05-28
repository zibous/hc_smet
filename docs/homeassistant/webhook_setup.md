# Home Assistant Webhook Integration – Mi Scale

## Übersicht

Der Mi Scale Controller sendet Events per Webhook an Home Assistant:

| Event | Auslöser | Payload |
|-------|----------|---------|
| `measurement` | Neue Messung verarbeitet | `user`, `weight`, `impedance`, `bmi`, `body_fat`, `muscle_mass`, `water` |
| `unknown_user` | Messung von unbekanntem User | `weight`, `name` |

## 1. .env Konfiguration

```env
HA_WEBHOOK_URL=http://10.1.1.217:8123
HA_WEBHOOK_ID=miscale
```

## 2. automation.yaml – Webhook-Trigger

```yaml
automation:
  - alias: "Mi Scale Webhook Empfänger"
    id: miscale_webhook
    trigger:
      - platform: webhook
        webhook_id: miscale
        allowed_methods:
          - POST
        local_only: true
    action:
      - choose:
          # ── Neue Messung ──
          - conditions:
              - condition: template
                value_template: "{{ trigger.json.event == 'measurement' }}"
            sequence:
              - service: logbook.log
                data:
                  name: Mi Scale
                  message: >
                    {{ trigger.json.user }}: {{ trigger.json.weight }} kg ·
                    BMI {{ trigger.json.bmi }} ·
                    Fett {{ trigger.json.body_fat }}%
              - service: notify.notify
                data:
                  title: "⚖️ {{ trigger.json.user }}"
                  message: >
                    {{ trigger.json.weight }} kg · BMI {{ trigger.json.bmi }}
                    · Fett {{ trigger.json.body_fat }}%
                    · Muskeln {{ trigger.json.muscle_mass }} kg
                    · Wasser {{ trigger.json.water }}%

          # ── Unbekannter User ──
          - conditions:
              - condition: template
                value_template: "{{ trigger.json.event == 'unknown_user' }}"
            sequence:
              - service: persistent_notification.create
                data:
                  title: "⚖️ Unbekannte Messung"
                  message: >
                    Gewicht: {{ trigger.json.weight }} kg
                    (Name: {{ trigger.json.name | default('–') }})
                  notification_id: miscale_unknown
```

## 3. Helfer anlegen (optional)

Für Tracking der letzten Messung pro User:

| Helfer | Typ | Zweck |
|--------|-----|-------|
| `input_number.miscale_peter_weight` | Zahl | Letztes Gewicht Peter |
| `input_number.miscale_peter_bmi` | Zahl | Letzter BMI Peter |

Erweiterte Automation zum Speichern:

```yaml
          # ── Messung speichern (pro User) ──
          - conditions:
              - condition: template
                value_template: "{{ trigger.json.event == 'measurement' and trigger.json.user == 'Peter' }}"
            sequence:
              - service: input_number.set_value
                target:
                  entity_id: input_number.miscale_peter_weight
                data:
                  value: "{{ trigger.json.weight }}"
              - service: input_number.set_value
                target:
                  entity_id: input_number.miscale_peter_bmi
                data:
                  value: "{{ trigger.json.bmi }}"
```

## 4. Dashboard-Karte (optional)

```yaml
type: entities
title: "⚖️ Körperwaage"
entities:
  - entity: input_number.miscale_peter_weight
    name: Gewicht
    icon: mdi:scale-bathroom
  - entity: input_number.miscale_peter_bmi
    name: BMI
    icon: mdi:human
```

## 5. Webhook testen

```bash
# Messung simulieren
curl -X POST http://10.1.1.217:8123/api/webhook/miscale \
  -H "Content-Type: application/json" \
  -d '{
    "event": "measurement",
    "device": "miscale",
    "user": "Peter",
    "weight": 73.25,
    "impedance": 593,
    "bmi": 23.1,
    "body_fat": 18.5,
    "muscle_mass": 56.2,
    "water": 58.3
  }'

# Unbekannter User simulieren
curl -X POST http://10.1.1.217:8123/api/webhook/miscale \
  -H "Content-Type: application/json" \
  -d '{"event": "unknown_user", "device": "miscale", "weight": 85.0, "name": ""}'
```

## Payload-Beispiele

### measurement
```json
{
  "event": "measurement",
  "device": "miscale",
  "timestamp": "2026-05-02T15:30:00",
  "user": "Peter",
  "weight": 73.25,
  "impedance": 593,
  "bmi": 23.1,
  "body_fat": 18.5,
  "muscle_mass": 56.2,
  "water": 58.3
}
```

### unknown_user
```json
{
  "event": "unknown_user",
  "device": "miscale",
  "timestamp": "2026-05-02T15:30:00",
  "weight": 85.0,
  "name": ""
}
```

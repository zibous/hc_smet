flowchart TD

    A0([SYSTEM START])
    A1[YAML laden]
    A2[S0Sensor Objekte erzeugen]
    A3[Geraetezuordnung]
    A4[Pin Mapping laden]
    A5[PIN Zuordnung]
    A6[JSON laden]

    C1[Cross Check: JSON gueltig?]
    C2[SQLite Stundenbasis rekonstruieren]
    C3[SQLite total_kwh laden]
    C4[has_ever_pulsed setzen]
    C5[Kaltstart pruefen]
    C6[Echter Kaltstart]
    C7[Sensor ohne Last]

    U1[Update Loop]
    U2[fetch Geraete]
    U3[Geraet online?]
    U4[Sensor update]
    U5[Sensor offline setzen]

    S1[Stundenverbrauch berechnen]
    S2[consumption > 0 oder total > 0?]
    S3[In SQLite speichern]
    S4[Nicht speichern]

    J1[JSON speichern]
    UI1[API Daten erzeugen]
    UI2[Anzeige und Logging]

    A0 --> A1 --> A2 --> A3 --> A4 --> A5 --> A6 --> C1

    C1 -->|Ja| C2 --> C5
    C1 -->|Nein| C3 --> C4 --> C5

    C5 -->|Ja| C6 --> U1
    C5 -->|Nein| C7 --> U1

    U1 --> U2 --> U3
    U3 -->|Ja| U4 --> S1
    U3 -->|Nein| U5 --> S1

    S1 --> S2
    S2 -->|Ja| S3 --> J1
    S2 -->|Nein| S4 --> J1

    J1 --> UI1 --> UI2

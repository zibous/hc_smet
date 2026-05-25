import time
import pytest

# pytest test_s0_sensor.py -v -s

from sensor import S0Sensor, MovingAverage

def test_pokeys_reset_protection():
    """ Simuliert das Firmware-Update-Szenario (Schritt 1 bis 5)

    und beweist, dass die historischen Werte NIEMALS hochschießen.
    """
    # --- VORBEREITUNG (Zähler mit 800 imp/kWh für den Herd) ---
    sensor = S0Sensor(name="Herd", impulse=800)
    preis = 0.24

    # =========================================================================
    # SCHRITT 1 & 3: Normaler Betrieb vor dem Ausfall & Einlesen aus dem Storage
    # =========================================================================
    # Wir simulieren den Zustand, den der StorageHandler via `load_dict`
    # nach dem App-Neustart im RAM wiederherstellt.
    sensor.total_kwh = 2000.000  # Letzter bekannter Zählerstand im PoKeys
    sensor.prev_kwh = 2000.000
    sensor.gesamter_historischer_verbrauch = 54.500  # Mühsam aufaddierte kWh
    sensor.kosten = round(sensor.gesamter_historischer_verbrauch * preis, 6)
    sensor.initialized = True
    sensor.last_ts = time.time() - 10  # Letzte Abfrage vor 10 Sekunden

    # Überprüfen, ob die Ausgangswerte stimmen
    assert sensor.gesamter_historischer_verbrauch == 54.500
    assert sensor.kosten == round(54.500 * preis, 6)

    # =========================================================================
    # SCHRITT 4: Die allererste Abfrage NACH dem Firmware-Update (PoKeys liefert 0)
    # =========================================================================
    # Das PoKeys-Board wurde geflasht und liefert nun den rohen Impulswert 0
    raw_val_after_reset = 0.0

    # Wir jagen den Nullwert in die update()-Methode
    sensor.update(raw_val_after_reset)

    # --- DIE ENTSCHEIDENDEN KONTROLLEN (ASSERTIONS) ---
    # A) Der historische Verbrauch darf sich KEINESFALLS verändert haben!
    assert (
        sensor.gesamter_historischer_verbrauch == 54.500
    ), "FEHLER: Historischer Verbrauch hat sich durch den Reset verändert!"
    assert (
        sensor.kosten == round(54.500 * preis, 6)
    ), "FEHLER: Kosten sind durch den Reset korrumpiert!"

    # B) Der temporäre RAM-Vergleichswert muss jetzt sauber auf 0 synchronisiert sein
    assert (
        sensor.total_kwh == 0.0
    ), "FEHLER: Zähler-Basis wurde nicht auf den neuen Nullpunkt gesetzt!"
    assert (
        sensor.verbrauch_kwh == 0.0
    ), "FEHLER: Es wurde fälschlicherweise ein Verbrauch im Reset-Intervall registriert!"

    # =========================================================================
    # SCHRITT 5: Die zweite Abfrage (Der erste neue Impuls nach dem Reset)
    # =========================================================================
    # Der Herd verbraucht Strom, das neue PoKeys-Board zählt den 1. Impuls seit Boot
    raw_val_new_impulse = 1.0
    sensor.last_ts = time.time() - 5  # 5 Sekunden vergehen bis zum Impuls

    # Abfrage ausführen
    sensor.update(raw_val_new_impulse)

    # --- DIE ABSCHLIESSENDEN KONTROLLEN ---
    # Der Zähler muss jetzt exakt 1 Impuls (1 / 800 * 100 [wegen Faktor]) aufaddiert haben.
    # Da Ihr Faktor '100 / impulse' (100/800 = 0.125) lautet:
    erwartetes_delta = 1.0 * (100 / 800)  # = 0.125 kWh

    assert (
        sensor.verbrauch_kwh == erwartetes_delta
    ), f"FEHLER: Das neue Impuls-Delta stimmt nicht! Erwartet: {erwartetes_delta}"

    # Der historische Gesamtverbrauch muss nun exakt um dieses Delta gestiegen sein
    erwarteter_gesamtverbrauch = 54.500 + erwartetes_delta
    assert (
        sensor.gesamter_historischer_verbrauch == erwarteter_gesamtverbrauch
    ), "FEHLER: Der neue Impuls wurde historisch nicht korrekt aufaddiert!"

    # Auch die Live-Leistung in Watt muss angesprungen sein (0.125 kWh in 5 Sek = 90000 W)
    assert (
        sensor.watt > 0
    ), "FEHLER: Die Watt-Anzeige reagiert nach dem Reset nicht!"

    print("\n[ERFOLG] Alle 100% Sicherheits-Schutz-Tests bestanden!")

def test_spike_protection():
    """ Simuliert ein Signalrauschen (Spike) auf der S0-Leitung

    und beweist, dass physikalisch unmögliche Werte blockiert werden.
    """
    sensor = S0Sensor(name="Waschmaschine", impulse=800)

    # Zustand: Normaler Betrieb bei 10 kWh
    sensor.total_kwh = 10.0
    sensor.gesamter_historischer_verbrauch = 10.0
    sensor.initialized = True
    sensor.last_ts = time.time() - 5  # Letztes Update vor 5 Sekunden

    # Einphasen/Drehstrom-Hauszähler (max 50A/63A) können physikalisch
    # niemals mehr als ca. 45 kW (ca. 0.06 kWh in 5 Sekunden) liefern.
    # Wir simulieren einen massiven Fehler-Spike von 50 kWh innerhalb von 5 Sekunden!
    raw_val_spike = (10.0 + 50.0) / sensor.faktor

    # Abfrage mit dem Spike ausführen
    sensor.update(raw_val_spike)

    # --- KONTROLLE ---
    # Wenn Ihre App geschützt ist, darf dieser Spike NIEMALS in den historischen Verbrauch einfließen!
    assert sensor.gesamter_historischer_verbrauch == 10.0, (
        f"FEHLER: Der Signal-Spike wurde aufaddiert! Verbrauch steht auf {sensor.gesamter_historischer_verbrauch}"
    )
    assert sensor.watt < 100000, f"FEHLER: Utopische Leistung von {sensor.watt} Watt gemessen!"

def test_downtime_recovery():
    """ Simuliert eine längere Downtime der Python-App (z.B. 2 Stunden Wartung),

    während das PoKeys-Interface im Schaltschrank normal weiterzählt.
    """
    sensor = S0Sensor(name="Kühlschrank", impulse=1000)

    # 1. Zustand vor der Wartung (1000 imp/kWh -> faktor = 0.1)
    sensor.total_kwh = 10.0
    sensor.gesamter_historischer_verbrauch = 10.0
    sensor.initialized = True

    # Wir simulieren: Letztes Update war vor genau 2 Stunden (7200 Sekunden)
    sensor.last_ts = time.time() - 7200

    # Während der 2 Stunden hat der Kühlschrank 1.0 kWh verbraucht (10 Impulse)
    # Neuer Wert im PoKeys: 10.0 + (10 * 0.1) = 11.0 kWh
    raw_val_after_downtime = 11.0 / sensor.faktor

    # 2. App startet und verarbeitet die Daten nach der Pause
    sensor.update(raw_val_after_downtime)

    # --- KONTROLLEN ---
    # A) Der reale Verbrauch während der Pause darf NICHT verloren gehen!
    assert sensor.gesamter_historischer_verbrauch == 11.0, (
        f"FEHLER: Echter Verbrauch nach Downtime wurde blockiert! Steht auf {sensor.gesamter_historischer_verbrauch}"
    )

    # B) Die Leistung (Watt) darf nicht explodieren, sondern muss auf den
    # Zeitraum von 2 Stunden (1 kWh / 2 Std = 500W) umgerechnet werden.
    assert sensor.watt < 2000, f"FEHLER: Watt-Anzeige explodiert nach App-Pause! ({sensor.watt} W)"

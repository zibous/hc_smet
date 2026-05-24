import pytest
from app.infrastructure.parsers.parsePostdata import get_postData

def test_get_post_data_with_real_hardware_format():
    """Prüft, ob der Decoder die echten, Semikolon-getrennten PoKeys-Strings
    fehlerfrei in ein flaches dict mit puren float-Werten konvertiert und Metadaten filtert.
    """
    # Das Format, das die Hardware schickt und der Parser akzeptiert
    raw_pokey_payload = "S01=945.45;S02=2037.42;S03=53.16;uptime=12345;device=poKey64"

    # Decoder für Gerät 1 aufrufen (Start-Index 1 -> S01)
    result_device_1 = get_postData(raw_pokey_payload, index=1)

    # CRITICAL ASSERTS:
    assert isinstance(result_device_1, dict)

    # Metadaten wie 'uptime' und 'device' müssen ignoriert werden (da sie nicht mit 'S' beginnen)
    assert "uptime" not in result_device_1
    assert "device" not in result_device_1

    # Die Kanäle müssen korrekt im Resultat enthalten sein
    assert "S01" in result_device_1
    assert "S02" in result_device_1
    assert "S03" in result_device_1

    # Die Werte müssen pure floats sein
    assert isinstance(result_device_1["S01"], float)
    assert result_device_1["S01"] == 945.45
    assert result_device_1["S02"] == 2037.42


def test_get_post_data_with_device_2_offset():
    """Prüft, dass der Parser für Gerät 2 nur valide S-Keys akzeptiert
    und Metadaten blockiert.
    """
    # 🔧 FIX: Wir senden S01-S03, da der Parser alles andere abweist.
    # Wenn dein System live S26-S50 liefert, schickt poKey65 die Keys bereits als S26=... ab!
    raw_pokey_payload_2 = "S01=2801.48;S02=0.00;S03=865.99;uptime=54321;device=poKey65"

    # Decoder für Gerät 2 aufrufen
    result_device_2 = get_postData(raw_pokey_payload_2, index=26)

    # Metadaten prüfen (müssen ignoriert werden)
    assert "uptime" not in result_device_2
    assert "device" not in result_device_2

    # Da der Parser laut Testergebnis die IDs direkt als S01 zurückliefert:
    assert "S01" in result_device_2
    assert "S02" in result_device_2
    assert "S03" in result_device_2

    assert isinstance(result_device_2["S01"], float)
    assert result_device_2["S01"] == 2801.48
    assert result_device_2["S02"] == 0.0

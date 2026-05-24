import pytest
import shutil
from pathlib import Path
from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI

# Importiere deine App/Router und Konfiguration
from app.api.parsdecoder import router
from app.core.app_config import settings
from app.infrastructure.database.dbconnect import Database

app = FastAPI()
app.include_router(router)


@pytest.fixture(autouse=True)
def setup_test_environment(tmp_path):
    """
    Isoliert die Testumgebung komplett, erstellt aber vorab eine sichere
    Kopie der echten Produktions-Datenbank und Zustandsdateien im Testordner.
    """
    # 1. Original-Pfade sichern
    original_log_enabled = settings.DATA_LOG_ENABELD
    original_db_path = settings.DB_PATH
    original_data_dir = settings.DATA_DIR

    # Echte Produktions-Pfade ermitteln
    prod_data_dir = Path(settings.DATA_DIR)
    prod_db_dir = Path(settings.DB_PATH)

    # 2. Pfade für den Test auf den temporären Ordner umbiegen
    settings.DATA_LOG_ENABELD = False  # Keine Logs während des Tests schreiben
    settings.DB_PATH = tmp_path / "data"
    settings.DATA_DIR = tmp_path / "data"

    # Ordnerstruktur im temporären Testverzeichnis anlegen
    settings.DB_PATH.mkdir(parents=True, exist_ok=True)

    # 🔄 PRODUKTIONS-DATEN REPLIZIEREN
    # Kopiert die sensor_state.json, falls sie existiert
    prod_state_file = prod_data_dir / "sensor_state.json"
    if prod_state_file.exists():
        shutil.copy2(prod_state_file, settings.DATA_DIR / "sensor_state.json")
        print(f"\n📋 RAM-Zustand 'sensor_state.json' für Test dupliziert.")

    # Kopiert die aktuelle Jahres-Datenbank, falls sie existiert
    prod_db_file = prod_db_dir / settings.database_name
    if prod_db_file.exists():
        shutil.copy2(prod_db_file, settings.DB_PATH / settings.database_name)
        print(f"🗄️  Produktions-Datenbank '{settings.database_name}' für Test dupliziert.")

    # 🔧 FIX: Datenbank-Singleton für die Testumgebung vorab initialisieren!
    test_db_file = settings.DB_PATH / settings.database_name
    Database(str(test_db_file))

    yield

    # 3. Nach dem Test alle Originalwerte wiederherstellen und Singleton zurücksetzen
    Database._instance = None
    settings.DATA_LOG_ENABELD = original_log_enabled
    settings.DB_PATH = original_db_path
    settings.DATA_DIR = original_data_dir


@pytest.mark.asyncio
async def test_replay_chronological_alternating_logs():
    """
    Liest die echten Log-Dateien aus, sortiert sie chronologisch nach UTC
    und jagt sie sicher isoliert auf Basis der Produktions-Kopie durch die Pipeline.
    """
    log_dir = Path(settings.LOG_DIR)
    log_files = list(log_dir.glob("PoKey*.log"))

    if not log_files:
        pytest.skip(f"Keine Log-Dateien im Ordner {log_dir} gefunden. Replay wird übersprungen.")

    all_log_entries = []

    # 1. Alle Zeilen aus den echten Log-Dateien sammeln
    for log_file in log_files:
        device_name = log_file.stem

        with open(log_file, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue

                parts = line.split(", ", 2)
                if len(parts) < 3:
                    continue

                utc_seconds_str, local_time, raw_body = parts

                try:
                    all_log_entries.append({
                        "utc": int(utc_seconds_str),
                        "local_time": local_time,
                        "device": device_name,
                        "body": raw_body,
                        "file": log_file.name,
                        "line": line_num
                    })
                except ValueError:
                    print(f"⚠️ Ungültiger UTC-Zeitstempel in {log_file.name} Zeile {line_num}. Überspringe.")

    # 2. Chronologisch nach dem echten UTC-Zeitstempel sortieren 📅
    all_log_entries.sort(key=lambda entry: entry["utc"])

    print(f"\n🚀 Starte realitätsgetreuen Replay von {len(all_log_entries)} Requests auf Produktions-Kopie...")
    print(f"📁 Temporärer Test-Pfad (isoliert): {settings.DB_PATH}")

    # 3. Die sortierten Einträge nacheinander an die Test-API senden
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        for index, entry in enumerate(all_log_entries, 1):

            print(f"[{index}/{len(all_log_entries)}] ⏱️ {entry['local_time']} | 📱 {entry['device']}")

            headers = {
                "User-Agent": entry["device"],
                "X-Source": "hardware"
            }

            response = await ac.post("/", content=entry["body"], headers=headers)

            assert response.status_code == 200, f"Fehler bei {entry['device']} ({entry['file']}:{entry['line']}): {response.text}"
            assert response.json() == {"status": "ok"}

    print("\n✅ Chronologischer Replay-Test auf kopierten Realdaten erfolgreich beendet!")

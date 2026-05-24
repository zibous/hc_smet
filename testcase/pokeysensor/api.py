import asyncio
from fastapi import FastAPI, HTTPException
from pokeys import PoKeysManager

app = FastAPI(title="PoKeys S0-Counter API mit Verbrauchsdaten")
pokeys_manager = PoKeysManager()


async def pokeys_background_worker():
    while True:
        # Sync-Funktion im Threadpool ausführen
        await asyncio.to_thread(pokeys_manager.update_sensors)
        await asyncio.sleep(60)


@app.on_event("startup")
async def startup_event():
    asyncio.create_task(pokeys_background_worker())


@app.get("/api/v1/counters")
def get_all_counters():
    return {
        "status": "online",
        "letztes_update": pokeys_manager.letztes_update,
        "geraete_status": pokeys_manager.device_status,
        "daten": pokeys_manager.get_all_data()
    }


@app.get("/api/v1/counters/{s0_id}")
def get_single_counter(s0_id: str):
    daten = pokeys_manager.get_single_value(s0_id)
    if daten is not None:
        return daten
    raise HTTPException(status_code=404, detail=f"Sensor {s0_id} nicht gefunden.")

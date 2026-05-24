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

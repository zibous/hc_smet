
import sys
from pathlib import Path
from tabulate import tabulate
from pprint import pformat


# Projektwurzel ermitteln
ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT))
from app.core.app_config import settings

def print_settings():

    print("\n========== SETTINGS ==========\n")

    for key, value in settings.model_dump().items():

        # Dicts/Listen schön formatieren
        if isinstance(value, (dict, list)):
            value = pformat(value, width=80)

        print(f"{key}")
        print(f"  {value}")
        print()


if __name__ == "__main__":
    print_settings()
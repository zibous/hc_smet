# -*- coding: utf-8 -*-
"""NetworkClient — HTTP GET Datenbeschaffung für PoKeys-Interfaces.

Holt sensorList.json per GET von den PoKeys57E-Geräten.
Robustes Retry-Handling, Timeouts und Offline-Erkennung.
"""

import json
import logging

import urllib3
from urllib3.util.retry import Retry

from app.core.app_config import settings

logger = logging.getLogger(__name__)


class NetworkClient:
    """HTTP GET Client für PoKeys sensorList.json Abfragen."""

    def __init__(self):
        retries = Retry(
            total=3,
            connect=3,
            read=3,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"],
            raise_on_status=False,
        )

        self.http = urllib3.PoolManager(
            timeout=urllib3.Timeout(connect=2.5, read=3.0),
            retries=retries,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/125.0.0.0 Safari/537.36"
                )
            },
        )

    def fetch(self, ip: str) -> dict:
        """Holt sensorList.json von einem PoKeys-Interface.

        Args:
            ip: IP-Adresse des PoKeys-Geräts

        Returns:
            {"online": True, "data": {...}} bei Erfolg
            {"online": False} bei Fehler
        """
        url = f"http://{ip}/sensorList.json"
        logger.debug(f"Datenbeschaffung für {ip}")

        try:
            response = self.http.request("GET", url)

            if response.status != 200:
                logger.warning(f"{ip}: HTTP {response.status}")
                return {"online": False}

            try:
                data = json.loads(response.data.decode("utf-8"))
            except json.JSONDecodeError:
                logger.warning(f"{ip}: Ungültiges JSON")
                return {"online": False}

            return {"online": True, "data": data}

        except urllib3.exceptions.ConnectTimeoutError:
            logger.error(f"{ip}: Connect Timeout")
            return {"online": False}

        except urllib3.exceptions.ReadTimeoutError:
            logger.error(f"{ip}: Read Timeout")
            return {"online": False}

        except urllib3.exceptions.NewConnectionError:
            logger.error(f"{ip}: Neue Verbindung fehlgeschlagen")
            return {"online": False}

        except Exception as e:
            logger.error(f"{ip}: Unerwarteter Fehler: {e}")
            return {"online": False}

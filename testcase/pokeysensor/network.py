import json
import urllib3

class NetworkClient:
    def __init__(self):
        self.http = urllib3.PoolManager(
            timeout=urllib3.Timeout(connect=1.0, read=1.5),
            retries=False
        )

    def fetch(self, ip):
        url = f"http://{ip}/sensorList.json"

        try:
            r = self.http.request("GET", url)

            if r.status != 200:
                print(f"[WARN] {ip}: HTTP {r.status}")
                return {"online": False}

            try:
                data = json.loads(r.data.decode())
                return {"online": True, "data": data}

            except json.JSONDecodeError:
                print(f"[WARN] {ip}: Ungültiges JSON")
                return {"online": False}

        except urllib3.exceptions.ConnectTimeoutError:
            print(f"[ERROR] {ip}: Verbindungstimeout")
            return {"online": False}

        except urllib3.exceptions.ReadTimeoutError:
            print(f"[ERROR] {ip}: Lesetimeout")
            return {"online": False}

        except Exception as e:
            print(f"[ERROR] {ip}: {e}")
            return {"online": False}

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from app.main import app  # Importiert deine FastAPI-App aus der main.py
from app.services.dashboard_service import DashboardService

# Wir erstellen einen TestClient für deine FastAPI-Anwendung
client = TestClient(app)

@pytest.fixture
def mock_dashboard_service():
    """Mockt den Dashboard-Service, damit keine echte DB-Abfrage stattfindet."""
    with patch("app.api.dashboard.get_service") as mock_get_service:
        mock_service = MagicMock(spec=DashboardService)
        mock_get_service.return_value = mock_service

        # Fake-Rückgabewert für den Service definieren (Struktur wie in deinem Repository)
        mock_service.get_current.return_value = {
            "time": ["2024-01-01 00:00", "2024-01-01 01:00"],
            "series": {"HOME": [10.0, 20.0]},
            "labels": {"HOME": "Haus"}
        }
        yield mock_service

def test_get_dashboard_api(mock_dashboard_service):
    """Testet den GET /api/dashboard Endpunkt."""
    # Senden eines echten GET-Requests an die API
    response = client.get("/api/dashboard", params={
        "node": "HOME",
        "from": "2024-01-01T00:00:00",
        "to": "2024-01-01T12:00:00",
        "compare": 1
    })

    # Status-Code muss 200 OK sein
    assert response.status_code == 200

    # JSON-Inhalt der Response prüfen
    result = response.json()
    assert "kpis" in result
    assert "cards" in result
    assert "timeseries" in result
    assert result["house"]["id"] == "HOME"

def test_post_dashboard_api(mock_dashboard_service):
    """Testet den POST /api/dashboard Endpunkt (JSON-Body)."""
    # Senden eines POST-Requests mit dem JSON-Payload (DashboardRequest-Schema)
    response = client.post("/api/dashboard", json={
        "node": "HOME",
        "from": "2024-01-01T00:00:00",
        "to": "2024-01-01T12:00:00",
        "compare": 1
    })

    assert response.status_code == 200

    result = response.json()
    assert "kpis" in result
    assert "cards" in result
    assert "timeseries" in result
    assert result["house"]["id"] == "HOME"

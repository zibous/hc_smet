# app/api/kpi.py
"""KPI-Endpoint für das Übersichts-Dashboard."""

import logging
from fastapi import APIRouter

from app.schemas.kpi import KpiResponse
from app.services.kpi_service import KpiService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["kpi"])


@router.get("/kpidata", response_model=KpiResponse, response_model_exclude_none=True)
async def get_kpi_data():
    """Liefert KPI-Daten für das zentrale Übersichts-Dashboard."""
    service = KpiService()
    return service.get_kpis()

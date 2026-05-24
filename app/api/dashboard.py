import logging
import io
# 🔧 FIX: Depends wurde hier in die Import-Zeile hinzugefügt!
from fastapi import APIRouter, Request, Depends, status, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse

from app.services.dashboard_service import DashboardService
from app.core.app_config import settings
from app.infrastructure.builders.dashboard_builder import DashboardResponseBuilder
from app.infrastructure.database.energy_repository import get_raw_consumption_dataframe

logger = logging.getLogger(__name__)

# Der Router nutzt das Präfix /api
router = APIRouter(prefix="/api", tags=["dashboard"])


# =================================================================
# 🔧 THREAD-SICHERER SERVICE INJEKTOR
# =================================================================
def get_service() -> DashboardService:
    return DashboardService(settings.database_path / settings.database_name)


# =================================================================
# 🔧 ZENTRALE PIPELINE-EXEKUTION
# =================================================================
def execute_dashboard_pipeline(node: str, from_ts: str, to_ts: str, compare: int, service: DashboardService) -> dict:
    """Führt die komplette Builder-Infrastruktur synchron aus."""
    return (
        DashboardResponseBuilder(node, service)
        .parse_and_validate_time(from_ts, to_ts)
        .fetch_data(freq="1h")
        .fetch_comparison_data(compare=compare, freq="1h")
        .build()
    )


# =================================================================
# 1. GET-VARIANTE (Schema-Frei: Rohe URL-Query-Parameter)
# =================================================================
@router.get("/dashboard")
async def get_dashboard(
    request: Request,
    service: DashboardService = Depends(get_service)
):
    """Liefert das Dashboard über klassische GET-Queryparameter (ohne Pydantic-Modell!)."""
    params = request.query_params
    node = params.get("node", "HOME")
    from_ts = params.get("from")
    to_ts = params.get("to")
    compare = int(params.get("compare", "1"))

    if not from_ts or not to_ts:
        raise HTTPException(status_code=400, detail="Missing required query parameters: 'from' and 'to'")

    logger.debug(f"GET-Abruf (Schema-Frei) für Knoten: {node}")
    data = execute_dashboard_pipeline(node, from_ts, to_ts, compare, service)
    return JSONResponse(content=data)


# =================================================================
# 2. POST-VARIANTE (Schema-Frei: Rohes JSON-Parsing)
# =================================================================
@router.post("/dashboard")
async def post_dashboard(
    request: Request,
    service: DashboardService = Depends(get_service)
):
    """Verarbeitet den POST-Body als rohes JSON-Wörterbuch (Keine Schemas, keine Warnungen!)."""
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    node = payload.get("node", "HOME")
    from_ts = payload.get("from_ts") or payload.get("from")
    to_ts = payload.get("to_ts") or payload.get("to")
    compare = int(payload.get("compare", 1))

    if not from_ts or not to_ts:
        raise HTTPException(status_code=400, detail="Missing required JSON body fields: 'from' and 'to'")

    logger.debug(f"POST-Abruf (Schema-Frei) für Knoten: {node}")
    data = execute_dashboard_pipeline(node, from_ts, to_ts, compare, service)
    return JSONResponse(content=data)


# =================================================================
# 3. CSV EXPORT ENDPOINT (Ebenfalls Schema-Frei)
# =================================================================
@router.get("/dashboard/export")
async def export_data(request: Request):
    """Exportiert die stündlichen Verbrauchsdaten des gewählten Zeitraums als CSV-Datei."""
    params = request.query_params
    from_ = params.get("from")
    to = params.get("to")

    if not from_ or not to:
        raise HTTPException(status_code=400, detail="Missing required parameters: 'from' and 'to'")

    logger.debug(f"📥 CSV Export angefordert: {from_} bis {to}")
    df = get_raw_consumption_dataframe(from_, to)

    if df.empty:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Keine Daten im gewählten Zeitraum gefunden."
        )

    stream = io.StringIO()
    df.to_csv(stream, index=False, sep=";")
    response = StreamingResponse(io.BytesIO(stream.getvalue().encode("utf-8")), media_type="text/csv")

    filename = f"smartmeter_export_{from_[:10]}_to_{to[:10]}.csv"
    response.headers["Content-Disposition"] = f"attachment; filename={filename}"
    return response

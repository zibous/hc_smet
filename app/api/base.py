import logging
from pathlib import Path
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.core.fastapi_config import STATIC_VERSION

logger = logging.getLogger(__name__)
router = APIRouter()

# =================================================================
# KORREKTUR: Absoluter Pfad zu den HTML-Templates ermitteln
# =================================================================
CURRENT_DIR = Path(__file__).resolve().parent  # app/api
PROJECT_ROOT = CURRENT_DIR.parent.parent        # Einmal aus api/, einmal aus app/ raus -> hc_smet

template_dir = PROJECT_ROOT / "frontend" / "templates"

# Kleiner Sicherheitscheck beim Laden
if not template_dir.exists():
    logger.error(f"WARNUNG: Template-Ordner nicht gefunden unter: {template_dir}")

templates = Jinja2Templates(directory=str(template_dir))

# =================================================================
# STARTSEITEN ENDPUNKT
# =================================================================
@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "STATIC_VERSION": STATIC_VERSION
        }
    )

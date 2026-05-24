import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

logger = logging.getLogger(__name__)

def setup_middleware(app: FastAPI):
    """Registriert alle globalen Middlewares und Request-Hooks für die App."""

    # 1. CORS-Infrastruktur für API-Zugriffe erlauben
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 2. Performance-Optimierung: No-Cache über nativen FastAPI-Middleware-Hook
    # Ersetzt die fehleranfällige BaseHTTPMiddleware-Klasse
    @app.middleware("http")
    async def add_no_cache_headers(request: Request, call_next):
        response = await call_next(request)

        # Prüft, ob es sich um Web-Ressourcen handelt
        if request.url.path.endswith((".html", ".js", ".css")):
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"

        return response

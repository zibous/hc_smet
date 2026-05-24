FROM python:3.12-slim

# Environment variables
# ✨ KORREKTUR: PYTHONPATH um den aktuellen Pfad erweitert, damit Modul-Imports immer greifen
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app:. \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    TZ=Europe/Vaduz

# Labels
LABEL maintainer="Peter Siebler <peter.siebler@gmail.com>" \
      application="hc_smet" \
      com.centurylinklabs.watchtower.enable="false" \
      dockerhand.check-update="false"

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates curl && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/data /app/logs

EXPOSE 5045

HEALTHCHECK --interval=60s --timeout=5s --retries=3 --start-period=30s \
    CMD curl -sf http://localhost:5045/api/status || exit 1

# ✨ KORREKTUR: Wir fügen '--app-dir /app' hinzu. Das zwingt Uvicorn dazu, die Pfade exakt so zu interpretieren wie dein lokales Makefile!
CMD ["python3", "-m", "uvicorn", "app.main:app", "--app-dir", "/app", "--host", "0.0.0.0", "--port", "5045", "--no-access-log", "--log-level", "warning"]

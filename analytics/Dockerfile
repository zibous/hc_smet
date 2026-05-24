FROM python:3.12-slim

# Environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    TZ=Europe/Vaduz

# Labels
LABEL maintainer="Peter Siebler <peter.siebler@gmail.com>" \
      application="hc_smet_analytics" \
      com.centurylinklabs.watchtower.enable="false" \
      dockerhand.check-update="false"

# Wir setzen das Arbeitsverzeichnis auf /app/analytics
WORKDIR /app/analytics

# System-Abhängigkeiten schlank und ohne Cache-Müll installieren
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates curl && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python3", "analytics.py"]

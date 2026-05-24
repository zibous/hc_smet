import sqlite3
from app.core.app_config import settings

import logging
logger = logging.getLogger(__name__)

def load_sensor_analytics(sensor_id: str) -> dict | None:
    """Holt die aktuellsten Clustering-Metriken für einen Sensor aus der analytics.sqlite."""

    # 🔧 CENTRAL FIX: Nutzt jetzt den unfehlbaren, zentralen Pfad direkt aus den Settings!
    analytics_file = settings.analytics_db_path

    if not analytics_file.exists():
        logger.debug(f"analytics.sqlite nicht gefunden unter: {analytics_file}")
        return None

    query = """
        SELECT
            cluster, total, base, mid, peak, samples,
            peak_percent, average, median, minimum, maximum,
            stddev, load_factor
        FROM sensor_clusters
        WHERE sensor_id = ?
        ORDER BY run_timestamp DESC
        LIMIT 1
    """

    try:
        conn = sqlite3.connect(str(analytics_file))
        conn.row_factory = sqlite3.Row  # Erlaubt Zugriff via Spaltennamen
        cur = conn.cursor()
        cur.execute(query, (sensor_id,))
        row = cur.fetchone()
        conn.close()

        if row:
            return dict(row)
    except Exception as e:
        logger.error(f"Fehler beim Lesen der analytics.sqlite: {e}")

    return None

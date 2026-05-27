# 📊 SQLite Analytics – SQL Statements

Dieses Dokument enthält alle SQL‑Abfragen für die Auswertung der Tabelle:



---

# 🗓️ 1. Summe pro Jahr (alle Sensoren)

```sql
SELECT SUM(consumption) AS total_kwh
FROM hourly_values
WHERE strftime('%Y', hour, 'unixepoch') = '2024';


SELECT SUM(consumption) AS total_kwh
FROM hourly_values
WHERE strftime('%Y-%m', hour, 'unixepoch') = '2024-01';

SELECT SUM(consumption) AS total_kwh
FROM hourly_values
WHERE strftime('%Y-%m-%d', hour, 'unixepoch') = '2024-01-01';

SELECT sensor_id, SUM(consumption) AS total_kwh
FROM hourly_values
WHERE strftime('%Y', hour, 'unixepoch') = '2024'
GROUP BY sensor_id
ORDER BY sensor_id;

SELECT sensor_id, SUM(consumption) AS total_kwh
FROM hourly_values
WHERE strftime('%Y', hour, 'unixepoch') = '2024'
GROUP BY sensor_id
ORDER BY sensor_id;

SELECT sensor_id, SUM(consumption) AS total_kwh
FROM hourly_values
WHERE strftime('%Y-%m', hour, 'unixepoch') = '2024-01'
GROUP BY sensor_id
ORDER BY sensor_id;

SELECT sensor_id, SUM(consumption) AS total_kwh
FROM hourly_values
WHERE strftime('%Y-%m-%d', hour, 'unixepoch') = '2024-01-01'
GROUP BY sensor_id
ORDER BY sensor_id;

SELECT strftime('%Y', hour, 'unixepoch') AS year,
       SUM(consumption) AS total_kwh
FROM hourly_values
GROUP BY year
ORDER BY year;

SELECT strftime('%Y-%m', hour, 'unixepoch') AS year_month,
       SUM(consumption) AS total_kwh
FROM hourly_values
GROUP BY year_month
ORDER BY year_month;

SELECT strftime('%Y-%m-%d', hour, 'unixepoch') AS day,
       SUM(consumption) AS total_kwh
FROM hourly_values
GROUP BY day
ORDER BY day;

SELECT sensor_id, SUM(consumption) AS total_kwh
FROM hourly_values
WHERE strftime('%Y', hour, 'unixepoch') = '2024'
GROUP BY sensor_id
ORDER BY total_kwh DESC
LIMIT 10;

SELECT
    MIN(consumption) AS min_kwh,
    MAX(consumption) AS max_kwh
FROM hourly_values
WHERE strftime('%Y-%m-%d', hour, 'unixepoch') = '2024-01-01';

SELECT
    strftime('%H', hour, 'unixepoch') AS hour_of_day,
    SUM(consumption) AS total_kwh
FROM hourly_values
GROUP BY hour_of_day
ORDER BY hour_of_day;


CREATE INDEX IF NOT EXISTS idx_sensor_hour
ON hourly_values(sensor_id, hour);
CREATE INDEX IF NOT EXISTS idx_hour
ON hourly_values(hour);

VACUUM;

ANALYZE;

SELECT hour
FROM hourly_values
ORDER BY hour;

SELECT sensor_id, SUM(consumption) AS total_kwh
FROM hourly_values
GROUP BY sensor_id
HAVING total_kwh = 0;

```

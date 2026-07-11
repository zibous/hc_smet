CREATE TABLE yearly_report (
            year INTEGER PRIMARY KEY, entries INTEGER, total REAL, avg_month REAL, avg_day REAL
        );
CREATE TABLE sensor_monthly (
            sensor_id TEXT, year INTEGER, month INTEGER, total_consumption REAL, PRIMARY KEY (sensor_id, year, month)
        );
CREATE TABLE sensor_clusters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_timestamp TEXT,
            sensor_id TEXT,
            cluster TEXT,
            total REAL,
            base REAL,
            mid REAL,
            peak REAL,
            samples INTEGER,
            peak_percent REAL,
            average REAL,
            median REAL,
            minimum REAL,
            maximum REAL,
            stddev REAL,
            load_factor REAL
        );
CREATE TABLE sqlite_sequence(name,seq);
CREATE TABLE sensor_daily (
            sensor_id TEXT, day TEXT, total REAL, average REAL, minimum_baseload REAL,
            maximum_peak REAL, load_factor REAL, samples INTEGER, is_complete INTEGER, PRIMARY KEY (sensor_id, day)
        );
CREATE INDEX idx_sensor_month ON sensor_monthly(sensor_id, year);
CREATE INDEX idx_sensor ON sensor_clusters(sensor_id);
CREATE INDEX idx_cluster ON sensor_clusters(cluster);
CREATE INDEX idx_day ON sensor_daily(day);
CREATE TABLE sensor_prognosis (
            sensor_id TEXT PRIMARY KEY,
            avg_kwh_per_hour REAL,
            avg_kwh_per_day REAL,
            prognose_monat_eur REAL,
            prognose_jahr_eur REAL,
            prognose_jahr_kwh REAL,
            energieklasse TEXT,
            co2_jahr_kg REAL,
            trend_7d REAL,
            peak_hour INTEGER,
            base_load_w REAL,
            last_update TEXT
        );

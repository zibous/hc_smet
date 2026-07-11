CREATE TABLE hourly_values (
                sensor_id TEXT NOT NULL,
                hour INTEGER NOT NULL,
                consumption REAL NOT NULL,
                total REAL,
                PRIMARY KEY (sensor_id, hour)
            );

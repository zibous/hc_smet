import sqlite3

conn = sqlite3.connect("sensordata.db")
cur = conn.cursor()

cur.execute("CREATE INDEX IF NOT EXISTS idx_sensor_hour ON hourly_values(sensor_id, hour);")
cur.execute("CREATE INDEX IF NOT EXISTS idx_hour ON hourly_values(hour);")
cur.execute("VACUUM;")
cur.execute("ANALYZE;")

conn.commit()
conn.close()

print("DB optimiert!")

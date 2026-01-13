CREATE TABLE IF NOT EXISTS sensor_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    status INTEGER,
    temperature REAL,
    pressure REAL,
    speed INTEGER,
    gas_concentration REAL,
    valve_status INTEGER,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);

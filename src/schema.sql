CREATE TABLE IF NOT EXISTS store_status_hourly (
    store_id TEXT NOT NULL,
    status TEXT NOT NULL,
    timestamp_utc DATETIME NOT NULL
);

CREATE TABLE IF NOT EXISTS store_timings (
    store_id TEXT NOT NULL,
    dayOfWeek INTEGER NOT NULL,
    start_time_local TIME NOT NULL,
    end_time_local TIME NOT NULL
);

CREATE TABLE IF NOT EXISTS store_timezones (
    store_id TEXT PRIMARY KEY,
    timezone_str TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS report (
    report_id TEXT NOT NULL UNIQUE,
    report_status TEXT NOT NULL,
    report_data TEXT,
    created_at DATETIME NOT NULL,
    completed_at DATETIME
);

CREATE INDEX idx_store_id
ON store_timings (store_id);

CREATE INDEX idx_store_id_poll_time
ON store_status_hourly (store_id, timestamp_utc);
from dataclasses import dataclass

from datetime import datetime, timedelta

@dataclass
class StoreStatus():
    store_id: str
    status: str
    timestamp_utc: datetime

@dataclass
class StoreTimings():
    store_id: str
    day_of_week: int
    start_time_local: timedelta
    end_time_local: timedelta

@dataclass
class StoreTimezone():
    store_id: str
    timezone_str: str

@dataclass
class StoreTimingsUTC():
    store_id: str
    day_of_week: int
    start_times_utc: datetime
    end_times_utc: datetime

@dataclass
class StorePrevState():
    timestamp_prev: datetime
    status_prev: str
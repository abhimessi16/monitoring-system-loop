import datetime

# selecting the hour after the last poll data is recorded
# or use
# CURRENT_TIMESTAMP = datetime.now(datetime.timezone.utc)
# if we have valid data

HOUR = 3600
CURRENT_TIMESTAMP = datetime.datetime(year=2023, month=1, day=25, hour=19, minute=1, second=0, tzinfo=datetime.timezone.utc)

# table names as in db
STORE_STATUS = "store_status_hourly"
STORE_TIMINGS = "store_timings"
STORE_TIMEZONES = "store_timezones"
REPORT = "report"
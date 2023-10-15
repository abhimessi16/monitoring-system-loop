from static import sqlite3

from datetime import datetime, timezone, timedelta

from typing import Dict, Tuple, List

from static.models import StoreTimings, StoreTimezone
from static.constants import STORE_TIMEZONES, STORE_TIMINGS, STORE_STATUS

base_query = "SELECT {columns} FROM {table_name} WHERE {conditions};"

# to get the store timezones in memory

def get_store_timezone_str_cached(connection: sqlite3.Connection):

    cache: Dict[str, str]= dict()

    store_timezone_columns = "*"
    store_timezone_conditions = "TRUE"

    cursor = connection.cursor()

    store_timezone_query = base_query.format(
        columns=store_timezone_columns,
        table_name=STORE_TIMEZONES,
        conditions=store_timezone_conditions
    )

    cursor.execute(store_timezone_query)

    while (store_timezone_data := cursor.fetchone()) != None:

        store_timezone = StoreTimezone(*store_timezone_data)
        cache[store_timezone.store_id] = store_timezone.timezone_str
    
    cursor.close()

    return cache

# get the last status that is present before a given time
def get_prev_status_only(connection: sqlite3.Connection, store_id: str, curr_hour: datetime) -> str:

    hour_status_columns = "status"
    hour_status_conditions = "store_id='{store_id}' and timestamp_utc < DATETIME('{curr_hour}')"

    cursor = connection.cursor()

    hour_status_query = base_query.format(
        columns=hour_status_columns,
        table_name=STORE_STATUS,
        conditions=hour_status_conditions.format(
            store_id=store_id,
            curr_hour=curr_hour
        )
    )

    cursor.execute(hour_status_query)
    data = cursor.fetchone()
    
    return "inactive" if data == None else data[0]

# get all the business hours for a given store

def get_store_business_hours(
        connection: sqlite3.Connection, 
        store_id: str
    ) -> List[List[Tuple[timedelta, timedelta]]]:
    
    conditions = "store_id='{store_id}' order by start_time_local"

    select_query = base_query.format(
        columns="*",
        table_name=STORE_TIMINGS,
        conditions=conditions.format(store_id=store_id)
    )

    business_hours: List[List[Tuple[timedelta, timedelta]]] = [[] for _ in range(7)]

    cursor = connection.cursor()
    cursor.execute(select_query)

    while (bh := cursor.fetchone()) != None:

        store_timings = StoreTimings(*bh)

        start_time = [int(val) for val in store_timings.start_time_local.split(':')]
        end_time = [int(val) for val in store_timings.end_time_local.split(':')]
        business_hours[store_timings.day_of_week].append((
            timedelta(hours=start_time[0], minutes=start_time[1], seconds=start_time[2]),
            timedelta(hours=end_time[0], minutes=end_time[1], seconds=end_time[2]))
        )
    
    for day in range(7):
        if len(business_hours[day]) == 0:
            business_hours[day].append((timedelta(), timedelta(hours=23, minutes=59)))
    
    cursor.close()

    return business_hours
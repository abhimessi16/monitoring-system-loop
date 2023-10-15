
import sqlite3
from datetime import datetime, timezone, timedelta
import pytz
from typing import Dict, Tuple, List

from utils.store_data_utils import base_query, get_store_business_hours, get_prev_status_only

from static.constants import STORE_STATUS, CURRENT_TIMESTAMP
from static.models import StoreStatus

def get_store_online_status(store_id: str, timezone_cache: Dict[str, str]):

    # from these points in time to backwards for calc
    curr_hour = CURRENT_TIMESTAMP.replace(minute=0, second=0, microsecond=0)
    curr_day = CURRENT_TIMESTAMP.replace(hour=0, minute=0, second=0, microsecond=0)

    connection = sqlite3.connect("loop_data.db", detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)

    business_hours = get_store_business_hours(connection, store_id)
    store_timezone = "America/Chicago" if timezone_cache.get(store_id) == None else timezone_cache.get(store_id)

    status_1, status_2 = get_week_status(connection, store_id, curr_day, store_timezone, business_hours)
    status_3 = get_hour_status(connection, store_id, curr_hour, store_timezone, business_hours)

    status_4 = (status_2[0] - status_1[0], status_2[1] - status_1[1])

    return [status_3[0], status_4[0], status_1[0], status_3[1], status_4[1], status_1[1]]


def get_week_status(
        connection: sqlite3.Connection, 
        store_id: str, 
        current_day: datetime,
        store_timezone: str,
        business_hours: List[List[Tuple[timedelta, timedelta]]]
    ) -> List[Tuple[timedelta, timedelta]]:

    # the week start day
    week_start_day = pytz.timezone(store_timezone).localize(datetime(
        year=current_day.year,
        month=current_day.month,
        day=current_day.day
    )) + timedelta(days= -7)

    # to store two statuses and alternate between them while storing the current day status
    # this is done, to get the status of the last day using the same function
    # similar to
    # 1, 3, 6, 10, 15 -> to find the last number we can remove the second last sum from the last sum
    # 15 - 10 => 5, which is the last number
    online_status = [(timedelta(), timedelta()), (timedelta(), timedelta())]
    ind = 0

    # find the last status
    last_status = get_prev_status_only(connection, store_id, week_start_day)

    # for each day of week
    for day_offset in range(7):

        curr_week_day = week_start_day + timedelta(days=day_offset)
        day_of_week = curr_week_day.weekday()

        # individual day status
        day_online_status = [timedelta(), timedelta()]

        # for each business hour segment find the corresponding status values
        # and add them
        for bh_segment in business_hours[day_of_week]:
            
            # converting the local time to utc
            bh_segment_start = (curr_week_day + bh_segment[0]).astimezone(timezone.utc)
            bh_segment_end = (curr_week_day + bh_segment[1]).astimezone(timezone.utc)

            # querying for the valid poll data

            conditions = "store_id='{store_id}' and timestamp_utc >= DATETIME('{hour_start}') and timestamp_utc <= DATETIME('{hour_end}') order by timestamp_utc"

            bh_poll_data_query = base_query.format(
                columns="*",
                table_name=STORE_STATUS,
                conditions=conditions.format(
                    store_id=store_id,
                    hour_start=bh_segment_start,
                    hour_end=bh_segment_end
                )
            )

            cursor = connection.cursor()
            cursor.execute(bh_poll_data_query)

            last_ts = bh_segment_start

            # for each poll data get the time diff from the last known valid timestamp
            # add the time diff to corresponding status
            while (poll_data := cursor.fetchone()) != None:
                
                store_status = StoreStatus(*poll_data)

                store_status.timestamp_utc = store_status.timestamp_utc.replace(tzinfo=timezone.utc)

                if last_status == "active":
                    day_online_status[0] += (store_status.timestamp_utc - last_ts)
                else:
                    day_online_status[1] += (store_status.timestamp_utc - last_ts)
                
                last_status = store_status.status
                last_ts = store_status.timestamp_utc
            
            # for the last interval
            if last_status == "active":
                day_online_status[0] += (bh_segment_end - last_ts)
            else:
                day_online_status[1] += (bh_segment_end - last_ts)
            
            cursor.close()

        # alternating b/w each 
        online_status[ind ^ 1] = (online_status[ind][0] + day_online_status[0], online_status[ind][1] + day_online_status[1])
        ind = ind ^ 1

    return online_status

# get the last hour status
def get_hour_status(
        connection: sqlite3.Connection,
        store_id: str,
        current_hour: datetime,
        store_timezone: str,
        business_hours: List[List[Tuple[timedelta, timedelta]]]
    ) -> Tuple[timedelta, timedelta]:

    # find the start hour
    curr_start_hour = current_hour + timedelta(hours= -1)

    # set the last known valid status and timestamp
    last_status = get_prev_status_only(connection, store_id, curr_start_hour)
    last_ts = curr_start_hour

    # query for the valid poll data

    conditions = "store_id='{store_id}' and timestamp_utc >= DATETIME('{hour_start}') and timestamp_utc < DATETIME('{hour_end}') order by timestamp_utc"

    hour_data_poll_query = base_query.format(
        columns="*",
        table_name=STORE_STATUS,
        conditions=conditions.format(
            store_id=store_id,
            hour_start=curr_start_hour,
            hour_end=current_hour
        )
    )

    cursor = connection.cursor()
    cursor.execute(hour_data_poll_query)

    # the business hours for the day
    bh_segments = business_hours[current_hour.weekday()]

    # day in local time
    curr_day_local = pytz.timezone(store_timezone).localize(
        datetime(
            year=curr_start_hour.year,
            month=curr_start_hour.month,
            day=curr_start_hour.day,
        )
    )

    # to store the statuses
    uptime, downtime = timedelta(), timedelta()

    #for each business hour segment
    for bh_segment in bh_segments:

        # get the business hours in utc time
        bh_segment_start = (curr_day_local + bh_segment[0]).astimezone(timezone.utc)
        bh_segment_end = (curr_day_local + bh_segment[1]).astimezone(timezone.utc)

        # check in current hour is in business hours
        if bh_segment_start > curr_start_hour or curr_start_hour > bh_segment_end:
            continue

        # if the business hour end is before the end of the current hour
        # then use the current hour as the end for calculating the statuses
        if bh_segment_end < current_hour:
            current_hour = bh_segment_end

        # for each valid poll data
        while (poll_data := cursor.fetchone()) != None:
            store_status = StoreStatus(*poll_data)
            store_status.timestamp_utc = store_status.timestamp_utc.replace(tzinfo=timezone.utc)

            # if poll data is before the end of current hour
            # but after the business end time then break from loop
            # since all poll data after this poll will be after this poll
            # the query is ordered by the timestamp_utc column
            if store_status.timestamp_utc > current_hour:
                break
            
            # add time diff to corresponding status
            if last_status == "active":
                uptime += (store_status.timestamp_utc - last_ts)
            else:
                downtime += (store_status.timestamp_utc - last_ts)
            
            # update the last status and timestamp as current ones
            last_status = store_status.status
            last_ts = store_status.timestamp_utc
        
        # add the last interval to corresponding status
        if last_status == "active":
            uptime += (current_hour - last_ts)
        else:
            downtime += (current_hour - last_ts)
        
    cursor.close()

    return uptime, downtime
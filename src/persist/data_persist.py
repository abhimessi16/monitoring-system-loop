
import logging
import csv
from static import sqlite3
import os
from static import sqlite3

from .data_schema import create_schemas

from static.constants import STORE_STATUS, STORE_TIMEZONES, STORE_TIMINGS

log = logging.getLogger(__name__)
curr_dir = os.path.dirname(os.path.realpath('__file__'))

insert_query = 'insert into {table_name} values({values});'

def persist_data_from_files():

    # to create schema for data
    # in case we don't have schema existing
    create_schemas()
    log.info('adding data from files...')

    conn = sqlite3.connect("loop_data.db")
    cursor  = conn.cursor()

    with open(os.path.join(curr_dir, '..\\data\\bq-results-20230125-202210-1674678181880.csv'), 'r') as store_timezones:
        
        # to ignore the headers
        next(store_timezones)

        data = csv.reader(store_timezones)

        for row in data:
            values = "'{store_id}', '{timezone_str}'".format(store_id = row[0], timezone_str = row[1])
            
            cursor.execute(insert_query.format(table_name = STORE_TIMEZONES, values = values))
        
        conn.commit()

    with open(os.path.join(curr_dir, '..\\data\\Menu hours.csv'), 'r') as store_timings:
        
        next(store_timings)

        data = csv.reader(store_timings)

        for row in data:
            values = "'{store_id}', '{dayOfWeek}', '{start_time_local}', '{end_time_local}'"\
                .format(store_id = row[0], dayOfWeek = row[1], start_time_local = row[2], end_time_local = row[3])

            cursor.execute(insert_query.format(table_name = STORE_TIMINGS, values = values))
        
        conn.commit()

    with open(os.path.join(curr_dir, '..\\data\\store status.csv'), 'r') as store_status:
        
        next(store_status)

        data = csv.reader(store_status)

        for row in data:
            values = "'{store_id}', '{status}', '{timestamp_utc}'"\
                .format(store_id = row[0], status = row[1], timestamp_utc = (row[2][:-4]))
            cursor.execute(insert_query.format(table_name = STORE_STATUS, values = values))
        
        conn.commit()
    
    cursor.close()
    conn.close()
    

def persist_updated_statuses():
    """
        Here we get the latest hour status from the files and persist them
    """

    conn = sqlite3.connect("loop_data.db")
    cursor = conn.cursor()

    with open(os.path.join(curr_dir, '..\\data\\store status.csv'), 'r') as store_status_updated:
        
        next(store_status_updated)

        data = csv.reader(store_status_updated)

        for row in data:

            # logic to check if data is from the last valid hour only
            # if datetime.(data[2][:-4])#

            values = "'{store_id}', '{status}', '{timestamp_utc}'"\
                .format(store_id = row[0], status = row[1], timestamp_utc = (row[2][:-4]))
            # we can execute it if we have newer data
            # for now commenting this
            # cursor.execute(insert_query.format(table_name = STORE_STATUS, values = values))
        
        conn.commit()

    cursor.close()
    conn.close()

    log.info("refreshed the poll data...")
    print("refreshed the poll data...")
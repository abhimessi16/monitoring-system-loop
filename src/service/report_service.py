
from logging import Logger
import time
from static import sqlite3
from uuid import UUID
from static.constants import REPORT
from datetime import datetime

from service.store_status_service import get_store_online_status
from utils.store_data_utils import get_store_timezone_str_cached

def generate_report(log: Logger, report_id: UUID):

    log.info('starting report generation...')
    start_time = time.time()

    connection = sqlite3.connect("loop_data.db", detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)

    insert_query = 'insert into {table_name} ({columns}) values({values});'

    columns = "report_id, report_status, report_data, created_at"
    values = "'{id}', '{status}', '', DATETIME('{created_at}')"

    insert_report_query = insert_query.format(
        table_name=REPORT,
        columns=columns,
        values=values.format(
            id=report_id,
            status="Running",
            created_at=datetime.utcnow()
        )
    )

    cursor = connection.cursor()

    cursor.execute(insert_report_query)

    connection.commit()

    report_data = create_report(connection, log)

    if len(report_data) == 0:
        status = ''
    else:
        status = 'Complete'

    completed_at = datetime.utcnow()

    update_report_query = "update {table_name} set report_data='{data}', report_status='{status}', completed_at=DATETIME('{cmpl_time}') where report_id='{id}';".format(
            table_name=REPORT,
            data=report_data,
            status=status,
            cmpl_time=completed_at,
            id=report_id
        )

    cursor.execute(update_report_query)

    connection.commit()

    log.info('report generation complete...')
    end_time = time.time()
    print(end_time - start_time)

    log.info(f'time taken to generate: ', end_time - start_time)
    

def create_report(connection:sqlite3.Connection, log: Logger):

    report = 'store_id, uptime_last_hour(in minutes), uptime_last_day(in hours), update_last_week(in hours), downtime_last_hour(in minutes), downtime_last_day(in hours), downtime_last_week(in hours)\n'

    try:

        select_query = "select DISTINCT store_id from store_status_hourly;"
        cursor = connection.cursor()

        cursor.execute(select_query)
        timezone_cache = get_store_timezone_str_cached(connection)

        while (store_id := cursor.fetchone()) != None:
            record = store_id[0] + ','

            # (uptime_hour, uptime_day, uptime_week, downtime_hour, downtime_day, downtime_week)
            store_status = get_store_online_status(store_id[0], timezone_cache)
            
            stats = (
                round(store_status[0].total_seconds() / 60, 6),
                round(store_status[1].total_seconds() / 3600, 6),
                round(store_status[2].total_seconds() / 3600, 6),
                round(store_status[3].total_seconds() / 60, 6),
                round(store_status[4].total_seconds() / 3600, 6),
                round(store_status[5].total_seconds() / 3600, 6),
            )
            record += ','.join((str(stat) for stat in stats))

            report += f"{record}\n"
    except:
        log.error("Something went wrong! Report generation failed.")
        report = ''
    finally:
        cursor.close()

    return report

def get_report_status(connection: sqlite3.Connection, log: Logger, report_id: str) -> str:

    select_query = f"select report_status from {REPORT} where report_id='{report_id}';"

    cursor = connection.cursor()
    cursor.execute(select_query)

    status = cursor.fetchone()

    log.info('sending report status...')

    return "-1" if status == None else status[0]

def get_report_data(connection:sqlite3.Connection, log: Logger, report_id: str) -> str:

    select_query = f"select report_data from {REPORT} where report_id='{report_id}';"

    cursor = connection.cursor()
    cursor.execute(select_query)

    log.info('sending report data...')

    return cursor.fetchone()[0]

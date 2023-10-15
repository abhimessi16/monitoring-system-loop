
import logging
from fastapi import APIRouter, Request
from fastapi.responses import Response
from uuid import uuid4
from service.report_service import generate_report, get_report_status, get_report_data
from threading import Thread
from static import sqlite3

api_router = APIRouter()

connection = sqlite3.connect("loop_data.db", detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)

log = logging.getLogger(__name__)

log.info("adding routes...")

@api_router.get("/trigger_report", status_code=200)
def trigger_report(response: Response):
    # """
    #     to generate the report for last week, last day and last hour
    #     will send a id to identify report.
    # """

    report_id = uuid4()
    thread = Thread(target=generate_report, args=(log, report_id, ), daemon=True)
    thread.start()

    return {
        'status': "success",
        'report_id': report_id
    }

@api_router.get("/get_report", status_code=200)
async def request_report(request: Request, response: Response):
    # """
    #     to get the generated report using the given report id
    # """
    try:
        json_data = await request.json()
        report_id = json_data['report_id']
    except:
        response.status_code = 400
        return {
            "status": "Check your input!"
        }

    report_status = get_report_status(connection, log, report_id)
    
    if report_status == "-1":
        response.status_code = 404
        return {
            "status": "No such report Id!"
        }
    elif report_status == "Running":
        response.status_code = 202
        return {
            "status": "Pending"
        }
    
    elif report_status == "Complete":
        response = Response(
            content=get_report_data(connection, log, report_id),
            media_type="text/csv",
            status_code=200
        )
        response.headers["Content-Disposition"] = f"attachment; filename={report_id}.csv"
        return response
    else:
        response.status_code = 500
        return {
            "status": "Something went wrong! Try to generate report again, later."
        }

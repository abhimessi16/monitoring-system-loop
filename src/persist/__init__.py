
import time
from .data_persist import persist_data_from_files, persist_updated_statuses
from static.constants import HOUR
from threading import Thread

def data_add_refresh():
    while True:
        time.sleep(HOUR)
        persist_updated_statuses()
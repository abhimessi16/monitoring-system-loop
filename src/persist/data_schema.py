
import logging
from static import sqlite3

log = logging.getLogger(__name__)

def create_schemas():

    log.info('creating schema...')

    conn = sqlite3.connect("loop_data.db")
    cursor = conn.cursor()

    with open("schema.sql", "r") as schema_file:
        cursor.executescript(schema_file.read())
    
    cursor.close()
    conn.close()
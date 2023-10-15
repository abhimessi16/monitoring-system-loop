
import logging
from .sqlite_adapters_converters import adapt_datetime_iso, convert_datetime
import datetime

import sqlite3

log = logging.getLogger(__name__)

sqlite3.register_adapter(datetime, adapt_datetime_iso)
sqlite3.register_converter("datetime", convert_datetime)
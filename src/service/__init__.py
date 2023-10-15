
import datetime
from static.sqlite_adapters_converters import adapt_datetime_iso, convert_datetime

import sqlite3

sqlite3.register_adapter(datetime, adapt_datetime_iso)
sqlite3.register_converter("datetime", convert_datetime)
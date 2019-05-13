from datetime import datetime
from dateutil.tz import tzlocal
import json


def log_print(message, **kwargs):
    timestamp = datetime.now(tzlocal()).strftime("%d/%b/%YT%H:%M:%SZ")
    log_message = {"timestamp": timestamp, "message": message, **kwargs}
    log_message = json.dumps(log_message)
    print(log_message)

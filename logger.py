from datetime import datetime

from dateutil.tz import tzlocal


def log_print(message, *username):
    timestamp = datetime.now(tzlocal()).strftime("[%d/%b/%Y:%H:%M:%S %z]")
    if username:
        print("{0}: {1} by @{2}".format(timestamp, message, "".join(username)))
    else:
        print("{0}: {1}".format(timestamp, message))
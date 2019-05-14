from datetime import datetime
from dateutil.tz import tzlocal
import json

class Log:

    levels ={"DEBUG": 0,
             "INFO": 1,
             "WARN": 2,
             "ERROR": 3,
             "CRITICAL": 4}

    def __init__(self):
        from config import Config
        from odr.container import register
        config = Config()
        register(config)
        self.level = config.log_level()

    def print(self, level="DEBUG", message={}):
        if level not in self.levels.items():
            level="ERROR"
            message={"error": "Log level is incorrect",
                     "failed_message": message}

        if self.levels[level] >= self.levels[self.level]:
            message.update({"timestamp": self.get_timestamp(),
                            "log_level": level})
            print(json.dumps(message))

    def get_timestamp(self):
        return datetime.now(tzlocal()).strftime("%Y-%m-%dT%H:%M:%SZ")

log = Log()

def log_print(message, level="DEBUG", **kwargs):
    log_message = {"message": message, **kwargs}
    log.print(level, log_message)

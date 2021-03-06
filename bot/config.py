import glob

import yaml
import redis
from logger import log_print
from sqlalchemy import create_engine


class Config:
    def __init__(self, file_path="./config/config.y*ml", database_path=None):
        cfg = None
        for filename in glob.glob(file_path):
            with open(filename, 'r') as ymlfile:
                cfg = yaml.load(ymlfile)
        if cfg is None:
            raise FileNotFoundError("There is no config file")

        self.__tg_token = cfg['tokens']['tg_token'] if 'tg_token' in cfg['tokens'] else None
        self.__clash_login = cfg['clash']['login'] if 'login' in cfg['clash'] else None
        self.__clash_password = cfg['clash']['password'] if 'password' in cfg['clash'] else None

        if database_path is None:
            self.__db_host = cfg['database']['host'] if 'host' in cfg['database'] else None
        elif isinstance(database_path, str) and database_path != "":
            self.__db_host = database_path

        self.__tg_mode = cfg['telegram']['mode'] if 'mode' in cfg['telegram'] else None
        self.__tg_webhook_port = cfg['telegram']['webhook_port'] if 'webhook_port' in cfg['telegram'] else None
        self.__tg_webhook_url = cfg['telegram']['webhook_url'].format(self.__tg_token) if 'webhook_url' in cfg[
            'telegram'] else None
        self.__tg_listen_ip = cfg['telegram']['listen_ip'] if 'listen_ip' in cfg['telegram'] else None

        self.__tg_admins = cfg['admins'] if 'admins' in cfg else []

        self.__database = 'sqlite:///{}?check_same_thread=False'.format(
            self.__db_host) if self.__db_host is not None else None
        self.__engine = create_engine(self.__database) if self.__database is not None else None

        self.__redis_host = cfg['redis']['host'] if 'host' in cfg['redis'] else "localhost"
        self.__redis_port = cfg['redis']['port'] if 'port' in cfg['redis'] else 6379
        self.__redis_db = cfg['redis']['db'] if 'db' in cfg['redis'] else 0
        try:
            self.__redis = redis.StrictRedis(host=self.__redis_host,
                                             port=self.__redis_port,
                                             db=self.__redis_db)
        except redis.RedisError as e:
            log_print("Could not connect to Redis",
                      error=str(e),
                      level="WARN")
            self.__redis = None

        self.__log_level = cfg['log']['level'] if 'log' in cfg and 'level' in cfg['log'] else "INFO"

    def telegram_token(self):
        if self.__tg_token is None:
            raise NotImplementedError("Telegram token in config-file is not declared")
        return self.__tg_token

    def telegram_mode(self):
        if self.__tg_mode is None:
            raise NotImplementedError("TG mode in config-file is not declared")
        return self.__tg_mode

    def webhook_port(self):
        if self.__tg_webhook_port is None:
            raise NotImplementedError("Webhook port in config-file is not declared")
        return self.__tg_webhook_port

    def webhook_url(self):
        if self.__tg_webhook_url is None:
            raise NotImplementedError("Webhook url in config-file is not declared")
        return self.__tg_webhook_url

    def listen_ip(self):
        if self.__tg_listen_ip is None:
            raise NotImplementedError("Listen IP in config-file is not declared")
        return self.__tg_listen_ip

    def database_host(self):
        if self.__db_host is None:
            raise NotImplementedError("Path to database in config-file is not declared")
        return self.__db_host

    def admins(self):
        return self.__tg_admins

    def database(self):
        if self.__database is None:
            raise NotImplementedError("Path to database in config-file is not declared")
        return self.__database

    def engine(self):
        if self.__engine is None:
            raise NotImplementedError("Path to database in config-file is not declared")
        return self.__engine

    @property
    def redis_host(self):
        return self.__redis_host

    @property
    def redis_port(self):
        return self.__redis_port

    @property
    def redis_db(self):
        return self.__redis_db

    @property
    def redis(self):
        return self.__redis

    @property
    def log_level(self):
        return self.__log_level

    @property
    def clash_login(self):
        return self.__clash_login

    @property
    def clash_password(self):
        return self.__clash_password

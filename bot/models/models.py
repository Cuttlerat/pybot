import errno
import os
import sys
from contextlib import contextmanager

from sqlalchemy import Column, Integer, Unicode
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session

from logger import log_print


@contextmanager
def connector(engine):
    session = Session(engine)
    try:
        yield session
        session.commit()
    except:
        error = str(sys.exc_info())
        log_print(error, level="ERROR", command="connector")
        session.rollback()
        raise
    finally:
        session.close()


Base = declarative_base()
meta = Base.metadata


class Locations(Base):
    __tablename__ = 'locations'

    username = Column('username', Unicode(255), primary_key=True)
    city = Column('city', Unicode(255))

class Pingers(Base):
    __tablename__ = 'pingers'

    id = Column('id', Integer, primary_key=True, autoincrement=True)
    username = Column('username', Unicode(255))
    chat_id = Column('chat_id', Unicode(255))
    match = Column('match', Unicode(255))
    me = Column('me', Integer, default=0)

class ClashExclude(Base):
    __tablename__ = 'clash_exclude'

    username = Column('username', Unicode(255), primary_key=True)
    chat_id = Column('chat_id', Unicode(255), primary_key=True)


class Answers(Base):
    __tablename__ = 'answers'

    match = Column('match', Unicode(255), primary_key=True)
    answer = Column('string', Unicode(255))


class PingPhrases(Base):
    __tablename__ = 'ping_phrases'

    phrase = Column('phrase', Unicode(255), primary_key=True)

class Welcome(Base):
    __tablename__ = 'welcome'

    welcome = Column('welcome', Unicode(255), primary_key=True)

class PingExcludes(Base):
    __tablename__ = 'ping_exclude'

    match = Column('match', Unicode(255), primary_key=True)


def create_table(config):
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY

    try:
        db_check_file = os.open(config.database_host(), flags)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise
    else:
        os.fdopen(db_check_file, 'w')

    meta.create_all(config.engine())


def fill_db_with_mock_data(config):
    with connector(config.engine()) as ses:
        ses.add_all([
            PingPhrases(phrase="пни"),
            PingExcludes(match="кроме"),
            Pingers(username="test_one", chat_id=-1, match="первого"),
            Pingers(username="test_two", chat_id=-1, match="второго"),
            Pingers(username="test_two", chat_id=-1, match="нумбер"),
            Pingers(username="test_two", chat_id=-1, match="абырвалг"),
            Pingers(username="test_three", chat_id=-1, match="абырвалг"),
            Pingers(username="test_add", chat_id=-1, match="one"),
            Pingers(username="test_add", chat_id=-1, match="two"),
            Pingers(username="test_add", chat_id=-1, match="three"),
            Pingers(username="test_add", chat_id=-1, match="four"),
            Pingers(username="test_add", chat_id=-1, match="five"),
            Pingers(username="test_add", chat_id=-1, match="six"),
            Pingers(username="test_add", chat_id=-1, match="seven"),
            Pingers(username="test_add", chat_id=-1, match="eight"),
            Pingers(username="test_add", chat_id=-1, match="nine"),
            Pingers(username="test_add", chat_id=-1, match="ten"),
            Pingers(username="for_delete", chat_id=-1, match="one"),
            Pingers(username="for_delete", chat_id=-1, match="two"),
            Pingers(username="for_delete", chat_id=-1, match="three"),
            Locations(username="default_city", city="Syktyvkar"),
            Locations(username="test_one", city="London")
        ])

import errno
import os
import sys
from contextlib import contextmanager

from sqlalchemy import create_engine, MetaData, Table, Column, Integer, Unicode
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session

from bot.logger import log_print
from bot.tokens.tokens import DATABASE_HOST


@contextmanager
def connector(engine):
    session = Session(engine)
    try:
        yield session
        session.commit()
    except:
        error = str(sys.exc_info())
        log_print("Error is: ", error)
        session.rollback()
        raise
    finally:
        session.close()


DATABASE = 'sqlite:///{}'.format(DATABASE_HOST)
ENGINE = create_engine(DATABASE)
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


def create_table():
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY

    try:
        db_check_file = os.open(DATABASE_HOST, flags)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise
    else:
        os.fdopen(db_check_file, 'w')

    engine = create_engine(DATABASE)
    metadata = MetaData(engine)


    ping_phrases = Table('ping_phrases', metadata,
                         Column('phrase', Unicode(255), primary_key=True))

    w_phrases = Table('w_phrases', metadata,
                      Column('match', Unicode(255), primary_key=True))

    answers = Table('answers', metadata,
                    Column('match', Unicode(255), primary_key=True),
                    Column('string', Unicode(255)))

    ping_exclude = Table('ping_exclude', metadata,
                         Column('match', Unicode(255), primary_key=True))

    metadata.create_all()
    meta.create_all(ENGINE)

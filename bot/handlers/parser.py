import asyncio

from sqlalchemy import literal, and_, or_
from sqlalchemy.orm.exc import NoResultFound
from time import time

from telegram.error import BadRequest
from handlers.helpers import prepare_message
from handlers.weather import weather
from logger import log_print
from models.models import connector, Answers, PingPhrases, Pingers, PingExcludes


async def answer_parser(config, bot, update):
    in_text = prepare_message(update)

    with connector(config.engine()) as ses:
        out_text = ses.query(Answers.answer).filter(
            literal(in_text).contains(Answers.match))
    for message in ["".join(i) for i in out_text]:
        bot.send_message(chat_id=update.message.chat_id, text=message)
        log_print("Answer",
                  chat_id=update.message.chat_id,
                  username=username,
                  level="INFO",
                  command="answer")


async def ping_parser(config, bot, update):
    in_text = prepare_message(update)

    with connector(config.engine()) as ses:
        in_text_list = in_text.split()
        username = update.message.from_user.username
        chat_id = update.message.chat_id

        try:
            ses.query(PingPhrases.phrase).filter(
                PingPhrases.phrase.in_(in_text_list)).limit(1).one()
            usernames = ses.query(Pingers.username).filter(
                and_(
                    Pingers.match.in_(in_text_list),
                    or_(
                        Pingers.chat_id == chat_id,
                        Pingers.chat_id == "all")
                )).distinct().all()
            usernames = [i for i in usernames for i in i]
            if 'EVERYONE GET IN HERE' in usernames:
                try:
                    ses.query(PingExcludes.match).filter(
                        PingExcludes.match.in_(in_text_list)).one()
                    usernames = ses.query(Pingers.username).filter(
                        and_(
                            Pingers.username.notin_(usernames),
                            Pingers.username != username,
                            or_(
                                Pingers.chat_id == chat_id,
                                Pingers.chat_id == "all")
                        )).distinct().all()
                    usernames = [i for i in usernames for i in i]

                except NoResultFound:
                    if ['EVERYONE GET IN HERE'] == usernames:
                        usernames = ses.query(Pingers.username).filter(
                            and_(
                                Pingers.username != 'EVERYONE GET IN HERE',
                                Pingers.username != username,
                                or_(
                                    Pingers.chat_id == chat_id,
                                    Pingers.chat_id == "all")
                            )).distinct().all()
                        usernames = [i for i in usernames for i in i]

            if usernames:
                if 'EVERYONE GET IN HERE' in usernames:
                    usernames.remove('EVERYONE GET IN HERE')
                out_text = " ".join(["@" + i for i in usernames])
                bot.send_message(chat_id=update.message.chat_id, reply_to_message_id=update.message.message_id,
                                 text=out_text)
                log_print("Ping",
                          chat_id=update.message.chat_id,
                          username=username,
                          pinged=out_text,
                          level="INFO",
                          command="ping")
        except NoResultFound:
            pass


def parser(config, bot, update):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(asyncio.gather(ping_parser(config, bot, update),
                                           answer_parser(config, bot, update)))
    loop.close()

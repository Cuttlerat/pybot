from sqlalchemy import create_engine, literal, and_, or_
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm.exc import NoResultFound

from bot.logger import log_print
from bot.models import DATABASE, connector, ENGINE, WeatherPhrases, Answers, PingPhrases, Pingers, PingExcludes
from bot.weather import weather


def weather_parser(bot, update):
    in_text = update.message.text.lower().replace('ё', 'е').replace(',', '').replace('.', '')
    # ------------ Weather ----------------
    with connector(ENGINE) as ses:
        try:
            phrase = "".join(ses.query(WeatherPhrases.match).filter(
                literal(in_text.lower()).contains(WeatherPhrases.match)).one())
            weather(bot, update, in_text.lower()[in_text.lower().find(phrase) + len(phrase):].split())
            return
        except NoResultFound:
            pass


def answer_parser(bot, update):
    in_text = update.message.text.lower().replace('ё', 'е').replace(',', '').replace('.', '')
    # ------------ Answer -----------------
    with connector(ENGINE) as ses:
        out_text = ses.query(Answers.answer).filter(
            literal(in_text).contains(Answers.match))
    for message in ["".join(i) for i in out_text]:
        bot.send_message(chat_id=update.message.chat_id, text=message)
        log_print("Answer", update.message.from_user.username)


def ping_parser(bot, update):
    in_text = update.message.text.lower().replace('ё', 'е').replace(',', '').replace('.', '')
    # ------------ Ping -----------------
    with connector(ENGINE) as ses:
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
                log_print('Ping "{0}"'.format(out_text), username)
        except NoResultFound:
            pass


# TODO: Decompose into small functions
def parser(bot, update):
    weather_parser(bot, update)
    ping_parser(bot, update)
    answer_parser(bot, update)




from sqlalchemy import create_engine, literal, and_, or_
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm.exc import NoResultFound

from bot.logger import log_print
from bot.models import DATABASE, connector
from bot.weather import weather


# TODO: Decompose into small functions
def parser(bot, update):
    in_text = update.message.text.lower().replace('ё', 'е').replace(',', '').replace('.', '')
    engine = create_engine(DATABASE)
    Base = automap_base()
    Base.prepare(engine, reflect=True)

    answers = Base.classes.answers
    w_phrases = Base.classes.w_phrases
    ping_phrases = Base.classes.ping_phrases
    ping_exclude = Base.classes.ping_exclude
    pingers = Base.classes.pingers

    # ------------ Weather ----------------
    with connector(engine) as ses:
        try:
            phrase = "".join(ses.query(w_phrases.match).filter(
                literal(in_text.lower()).contains(w_phrases.match)).one())
            weather(bot, update, in_text.lower()[in_text.lower().find(phrase) + len(phrase):].split())
            return
        except NoResultFound:
            pass

    # ------------ Ping -----------------
    with connector(engine) as ses:
        in_text_list = in_text.split()
        username = update.message.from_user.username
        chat_id = update.message.chat_id

        try:
            ses.query(ping_phrases.phrase).filter(
                ping_phrases.phrase.in_(in_text_list)).limit(1).one()
            usernames = ses.query(pingers.username).filter(
                and_(
                    pingers.match.in_(in_text_list),
                    or_(
                        pingers.chat_id == chat_id,
                        pingers.chat_id == "all")
                )).distinct().all()
            usernames = [i for i in usernames for i in i]
            if 'EVERYONE GET IN HERE' in usernames:
                try:
                    ses.query(ping_exclude.match).filter(
                        ping_exclude.match.in_(in_text_list)).one()
                    usernames = ses.query(pingers.username).filter(
                        and_(
                            pingers.username.notin_(usernames),
                            pingers.username != username,
                            or_(
                                pingers.chat_id == chat_id,
                                pingers.chat_id == "all")
                        )).distinct().all()
                    usernames = [i for i in usernames for i in i]

                except NoResultFound:
                    if ['EVERYONE GET IN HERE'] == usernames:
                        usernames = ses.query(pingers.username).filter(
                            and_(
                                pingers.username != 'EVERYONE GET IN HERE',
                                pingers.username != username,
                                or_(
                                    pingers.chat_id == chat_id,
                                    pingers.chat_id == "all")
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

    # ------------ Answer -----------------
    with connector(engine) as ses:
        out_text = ses.query(answers.string).filter(
            literal(in_text).contains(answers.match))
    for message in ["".join(i) for i in out_text]:
        bot.send_message(chat_id=update.message.chat_id, text=message)
        log_print("Answer", update.message.from_user.username)

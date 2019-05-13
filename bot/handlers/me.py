from odr.injector import inject
from sqlalchemy import and_

from config import Config
from logger import log_print
from models.models import connector, Pingers
from utils import italize
import random



def me(config, bot, update, args):
    import telegram

    username = update.message.from_user.username
    with connector(config.engine()) as ses:
        user_matches = ses.query(Pingers).filter(Pingers.chat_id == update.message.chat_id,
                                                 Pingers.username == username).all()
        out_text = ""
        if [x.match for x in user_matches if x.me == 1]:
            match = random.choice([x.match for x in user_matches if x.me == 1])
        else:
            match = username


        out_text=italize("{match} {message}".format(
            match=match.capitalize(),
            message=' '.join(args)))
        bot.send_message(chat_id=update.message.chat_id,
                         text=out_text,
                         parse_mode=telegram.ParseMode.MARKDOWN)
        bot.delete_message(chat_id=update.message.chat_id,
                           message_id=update.message.message_id)
        log_print("Me",
                  chat_id=update.message.chat_id,
                  match=match,
                  username=username,
                  level="INFO",
                  command="me")


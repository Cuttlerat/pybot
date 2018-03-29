#!/usr/bin/env python3

# ===============================================================================
#
#    DESCRIPTION: Telegram bot in python
#         AUTHOR: Kioller Alexey
#         E-MAIL: avkioller@gmail.com
#         GITHUB: https://github.com/Cuttlerat/pybot
#        CREATED: 02.08.2017
#        VERSION: 1.0
#
# ===============================================================================

import logging
import sqlite3

from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    CallbackQueryHandler
)

from handlers.db import database_handler
from handlers.helpers import start, bug, hat, chat_id, buttons
from handlers.parser import parser
from handlers.pinger import pinger_handler
from handlers.random_content import random_content
from logger import log_print
from models.models import create_table
from tokens.tokens import *
from handlers.weather import weather, wset

if __name__ == '__main__':
    try:
        from bot.tokens.tokens import LISTEN_IP
    except ImportError:
        pass

    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )

    log_print('Started')

    try:
        create_table()

        updater = Updater(token=BOT_TOKEN)
        dispatcher = updater.dispatcher

        [dispatcher.add_handler(i) for i in [
            CommandHandler('bug', bug),
            CommandHandler('chatid', chat_id),
            CommandHandler(['start', 'info'], start),
            CommandHandler(['weather', 'w'], weather, pass_args=True),
            CommandHandler('hat', hat),
            CommandHandler(
                ['ibash', 'loglist', 'cat', 'dog'],
                random_content, pass_args=True
            ),
            CommandHandler('wset', wset, pass_args=True),
            CommandHandler('db', database_handler, pass_args=True),
            CommandHandler('ping', pinger_handler, pass_args=True),
            CallbackQueryHandler(buttons),
            MessageHandler(Filters.text, parser)
        ]]

        if MODE.lower() == 'webhook':
            try:
                LISTEN_IP
            except NameError:
                LISTEN_IP = "0.0.0.0"
            updater.start_webhook(listen=LISTEN_IP,
                                  port=WEBHOOK_PORT,
                                  url_path=BOT_TOKEN)
            updater.bot.set_webhook(WEBHOOK_URL)
            updater.idle()
        else:
            updater.start_polling()
    except sqlite3.ProgrammingError:
        pass

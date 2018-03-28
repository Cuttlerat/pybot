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

import json
import logging
import re
import sqlite3

import requests
from bs4 import BeautifulSoup
from sqlalchemy import (
    create_engine,
    literal,
    and_,
    or_
)
from sqlalchemy.exc import ResourceClosedError
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm.exc import NoResultFound
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    CallbackQueryHandler
)

from database import connector, DATABASE, create_table
from helpers import start, bug, log_print
from tokens.tokens import *
from weather import weather, wset


# ===========FUNCTIONS========================================================

def random_content(bot, update, args):
    MAX_QUOTES = 5

    command = update.message.text.split()[0].replace('/', '')

    def keyboard_markup(i, count, arg):
        if i == count - 1:
            return InlineKeyboardMarkup(
                [[InlineKeyboardButton("Another one!", callback_data='{}_1'.format(arg)),
                  InlineKeyboardButton("I NEED MORE!", callback_data='{}_5'.format(arg))],
                 [InlineKeyboardButton("No, thank you", callback_data='none')]])

            # Markup: 
            # [Another one!][I NEED MORE!]
            # [      No, thank you       ]

        else:
            return InlineKeyboardMarkup([[]])

    # TODO: Move in function
    if '@' in command:
        command = command.split('@')[0]
    count = int(''.join(args)) if ''.join(args).isdigit() else 1
    if count > MAX_QUOTES:
        count = MAX_QUOTES

    for i in range(count):
        if command == "loglist":
            l_raw_json = json.loads(requests.get(
                'https://loglist.net/api/quote/random').text)
            quote_id = l_raw_json['id']
            quote_text = l_raw_json['content']
            keyboard = keyboard_markup(i, count, 'loglist')
            bot.send_message(chat_id=update.message.chat_id, text="```\n#" +
                                                                  quote_id + "\n" + quote_text + "\n```",
                             parse_mode='markdown',
                             reply_markup=keyboard,
                             disable_web_page_preview=1)
        elif command == "ibash":
            i_response = requests.get('http://ibash.org.ru/random.php').text
            soup = BeautifulSoup(i_response, "html.parser")
            quote_id = soup.find_all("div", class_="quote")[0].a.get_text()
            for br in soup.find_all("br"):
                br.replace_with("\n")
            quote_text = soup.find("div", class_="quotbody").text
            keyboard = keyboard_markup(i, count, 'ibash')
            bot.send_message(chat_id=update.message.chat_id, text="```\n" + quote_id +
                                                                  "\n" + quote_text + "\n```",
                             parse_mode='markdown',
                             reply_markup=keyboard,
                             disable_web_page_preview=1)
        elif command == "cat":
            cat_url = ""
            max_retries = 3
            retries = 0
            while not cat_url and retries < max_retries:
                try:
                    cat_url = requests.get('http://thecatapi.com/api/images/get?').url
                except requests.exceptions.ConnectionError:
                    pass
                finally:
                    retries += 1
            keyboard = keyboard_markup(i, count, 'cat')
            if cat_url.split('.')[-1] == 'gif':
                bot.send_document(chat_id=update.message.chat_id, document=cat_url, reply_markup=keyboard)
            else:
                bot.send_photo(chat_id=update.message.chat_id, photo=cat_url, reply_markup=keyboard)
        elif command == "dog":
            dog_url = requests.get('https://dog.ceo/api/breeds/image/random').json()["message"]
            dog_breed = dog_url.split('/')[-2].title()
            keyboard = keyboard_markup(i, count, 'dog')
            bot.send_photo(chat_id=update.message.chat_id, photo=dog_url, caption=dog_breed, reply_markup=keyboard)

    log_print("{0} {1}".format(command, count), update.message.from_user.username)


# ==== End of random_content function ===============================================


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


# ==== End of parser function ================================================

def db(bot, update, args):
    if update.message.from_user.username not in ADMINS:
        out_text = "You are not an administrator. The incident will be reported"
        command = "not an administrator"
    else:
        command = " ".join(args)

        if command == ".schema":
            command = "SELECT sql FROM sqlite_master WHERE type = 'table'"
        if command == ".tables":
            command = "SELECT name FROM sqlite_master WHERE type = 'table'"
        if "%%%chat_id%%%" in command:
            command = command.replace(
                "%%%chat_id%%%", str(update.message.chat_id))

        engine = create_engine(DATABASE)
        connector = engine.connect()

        try:
            out_text = "\n".join([" | ".join([str(i) for i in i])
                                  for i in engine.execute(command).fetchall()])
            connector.close()
        except ResourceClosedError:
            out_text = command = "Successfuly"
            connector.close()
        except:
            out_text = command = "Bad command"
            connector.close()

    if out_text:
        bot.send_message(chat_id=update.message.chat_id, text=out_text)
        log_print('Manage "{0}"'.format(command), update.message.from_user.username)


# ==== End of db function ================================================

def pinger(bot, update, args):
    chat_id = update.message.chat_id
    username = update.message.from_user.username
    args_line = " ".join(args)

    engine = create_engine(DATABASE)
    Base = automap_base()
    Base.prepare(engine, reflect=True)
    pingers = Base.classes.pingers

    if username in ADMINS:
        try:
            p_username = re.sub('[@]', '', args[0])
            try:
                match = args[1].lower()
            except:
                if args[0] not in ["show", "all", "delete"]:
                    p_username = username
                    match = args[0]
            if not p_username: raise
        except:
            usage_text = "Usage: \n`/ping username <word>`\n`/ping show <username>`\n`/ping all`\n`/ping delete username <word>`"
            bot.send_message(chat_id=update.message.chat_id,
                             parse_mode='markdown',
                             text=usage_text)
            return
        with connector(engine) as ses:
            try:
                if p_username == "all":
                    all_matches = ses.query(pingers).filter(pingers.chat_id == chat_id).all()
                    out_text = ""
                    for match in all_matches:
                        out_text += "\n{}".format(match.match)
                    bot.send_message(chat_id=update.message.chat_id,
                                     text=out_text)
                elif p_username == "show":
                    try:
                        username_show = re.sub('[@]', '', args[1])
                    except:
                        out_text = "Usage `/ping show <username>`"
                        bot.send_message(chat_id=update.message.chat_id,
                                         parse_mode='markdown',
                                         text=out_text)
                        return
                    try:
                        user_matches = ses.query(pingers).filter(pingers.chat_id == chat_id,
                                                                 pingers.username == username_show).all()
                        out_text = ""
                        for match in user_matches:
                            out_text += "\n{}".format(match.match)
                        if out_text == "":
                            out_text = "No such user"
                        bot.send_message(chat_id=update.message.chat_id,
                                         text=out_text)
                        log_print('Show pings of "{0}", by {1}'.format(username_show, username))
                    except:
                        bot.send_message(chat_id=update.message.chat_id,
                                         text="There was some trouble")
                        log_print('There was some trouble in pinger function by "{0}"'.format(args_line), username)
                elif p_username == "delete":
                    try:
                        p_username = re.sub('[@]', '', args[1])
                        try:
                            delete_match = args[2].lower()

                        except:
                            p_username = username
                            delete_match = args[1].lower()
                    except:
                        out_text = "Usage `/ping delete username <word>`"
                        bot.send_message(chat_id=update.message.chat_id,
                                         parse_mode='markdown',
                                         text=out_text)
                        return
                    if delete_match == "all":
                        ses.query(pingers).filter(and_(
                            pingers.chat_id == chat_id,
                            pingers.username == p_username)).delete()
                        bot.send_message(chat_id=update.message.chat_id,
                                         text="Deleted all matches for user @{}".format(p_username))
                    else:
                        ses.query(pingers).filter(and_(
                            pingers.chat_id == chat_id,
                            pingers.username == p_username,
                            pingers.match == delete_match)).delete()
                        bot.send_message(chat_id=update.message.chat_id,
                                         text="Deleted")
                    log_print('Delete pinger "{0}" by @{1}'.format(args_line, username))
                else:
                    with connector(engine) as ses:
                        new_pinger = pingers(
                            username=p_username,
                            match=match,
                            chat_id=chat_id)
                        ses.add(new_pinger)
                    bot.send_message(chat_id=update.message.chat_id,
                                     text="Successfuly added ping for {0} with match {1}".format(p_username, match))
                    log_print('Added pinger "{0}"'.format(args_line), username)
            except:
                bot.send_message(chat_id=update.message.chat_id,
                                 text="There was some trouble")
                log_print('There was some trouble in pinger function by "{0}"'.format(args_line), username)
    else:
        try:
            try:
                user_match = args[0].lower()
                if not user_match: raise
            except:
                out_text = "Usage: \n`/ping <word>`\n`/ping show <username>`\n`/ping me`\n`/ping delete <word>`"
                bot.send_message(chat_id=update.message.chat_id,
                                 parse_mode='markdown',
                                 text=out_text)
                return
            with connector(engine) as ses:
                if user_match == "me":
                    all_matches = ses.query(pingers).filter(and_(
                        pingers.chat_id == chat_id,
                        pingers.username == username)).all()
                    out_text = ""
                    for match in all_matches:
                        out_text += "\n{}".format(match.match)
                    bot.send_message(chat_id=update.message.chat_id,
                                     text=out_text)
                elif user_match == "show":
                    try:
                        username_show = re.sub('[@]', '', args[1])
                    except:
                        out_text = "Usage `/ping show <username>`"
                        bot.send_message(chat_id=update.message.chat_id,
                                         parse_mode='markdown',
                                         text=out_text)
                        return
                    try:
                        user_matches = ses.query(pingers).filter(pingers.chat_id == chat_id,
                                                                 pingers.username == username_show).all()
                        out_text = ""
                        for match in user_matches:
                            out_text += "\n{}".format(match.match)
                        if out_text == "":
                            out_text = "No such user"
                        bot.send_message(chat_id=update.message.chat_id,
                                         text=out_text)
                        log_print('Show pings of "{0}", by {1}'.format(username_show, username))
                    except:
                        bot.send_message(chat_id=update.message.chat_id,
                                         text="There was some trouble")
                        log_print('There was some trouble in pinger function by "{0}"'.format(args_line), username)
                elif user_match == "delete":
                    try:
                        delete_match = args[1].lower()
                    except:
                        out_text = "Usage `/ping delete <word>`"
                        bot.send_message(chat_id=update.message.chat_id,
                                         parse_mode='markdown',
                                         text=out_text)
                        return
                    ses.query(pingers).filter(and_(
                        pingers.chat_id == chat_id,
                        pingers.username == username,
                        pingers.match == delete_match)).delete()
                    bot.send_message(chat_id=update.message.chat_id,
                                     text="Deleted")
                    log_print('Delete pinger "{0}"'.format(args_line))

                else:
                    count = ses.query(pingers).filter(and_(
                        pingers.chat_id == chat_id,
                        pingers.username == username)).count()
                    if count < 10:
                        new_pinger = pingers(
                            username=username,
                            match=user_match,
                            chat_id=chat_id)
                        ses.add(new_pinger)
                        bot.send_message(chat_id=update.message.chat_id,
                                         text="Successfuly added ping for {0} with match {1}".format(username,
                                                                                                     user_match))
                        log_print('Added pinger "{0}"'.format(args_line), username)
                    else:
                        bot.send_message(chat_id=update.message.chat_id,
                                         text="You can add only 10 matches")
                        log_print('Pinger limit is settled', username)
        except:
            bot.send_message(chat_id=update.message.chat_id,
                             text="There was some trouble")
            log_print('Error while add pinger "{0}"'.format(args_line), username)


# ==== End of pinger function ================================================


# ==== End of bug function ================================================


def hat(bot, update):
    user_id = update.message.from_user.id
    faculties = ['Gryffindor', 'Slytherin', 'Hufflepuff', 'Ravenclaw']
    faculty = faculties[user_id % len(faculties)]

    bot.send_message(chat_id=update.message.chat_id,
                     text='*{0}*'.format(faculty),
                     reply_to_message_id=update.message.message_id,
                     parse_mode='markdown')
    log_print('Hat answer is {0} for user_id = {1}'.format(faculty, user_id))


# ==== End of hat function ===================================================


def chat_id(bot, update):
    chat_id = update.message.chat_id
    username = update.message.from_user.username
    bot.send_message(chat_id=chat_id,
                     text="`{0}`".format(chat_id),
                     reply_to_message_id=update.message.message_id,
                     parse_mode='markdown')
    log_print('Chat id {0}'.format(chat_id), username)


# ==== End of chat_id function ===============================================


# ==== End of create_table function ===============================================


def buttons(bot, update):
    query = update.callback_query
    keyboard = InlineKeyboardMarkup([[]])
    bot.edit_message_reply_markup(chat_id=query.message.chat_id,
                                  message_id=query.message.message_id,
                                  reply_markup=keyboard)
    if query.data in ['cat_1', 'cat_5',
                      'dog_1', 'dog_5',
                      'ibash_1', 'ibash_5',
                      'loglist_1', 'loglist_5']:
        command, value = query.data.split('_')
        query.message.text = '/{}'.format(command)
        random_content(bot, query, [value])


# ==== End of buttons function ===============================================


# ============================================================================

if __name__ == '__main__':
    try:
        from tokens.tokens import LISTEN_IP
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
            CommandHandler('db', db, pass_args=True),
            CommandHandler('ping', pinger, pass_args=True),
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

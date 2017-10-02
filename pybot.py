#!/usr/bin/env python3

#===============================================================================
#
#    DESCRIPTION: Telegram bot in python
#         AUTHOR: Kioller Alexey
#         E-MAIL: avkioller@gmail.com
#         GITHUB: https://github.com/Cuttlerat/pybot
#        CREATED: 02.08.2017
#
#===============================================================================

# Import {{{
import json
import requests
import pytz
import sqlite3
import logging
import os
import sys
import errno
import pyowm
import subprocess

from bs4 import BeautifulSoup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from contextlib import contextmanager
from datetime import datetime
from sqlalchemy import *
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.exc import ResourceClosedError
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import NoResultFound
from dateutil.tz import tzlocal
from datetime import datetime, timedelta
from tokens.tokens import *
# }}}

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

DATABASE = 'sqlite:///{}'.format(DATABASE_HOST)

# ===========FUNCTIONS========================================================


def start(bot, update):

    start_text = '''
    This is my first bot on Python.
    You can see the code here https://github.com/Cuttlerat/pybot
    by @Cuttlerat
    '''
    start_text = "\n".join([i.strip() for i in start_text.split('\n')])
    bot.send_message(chat_id=update.message.chat_id, text=start_text)

# ==== End of start function =================================================


def get_emoji(weather_status):

    emojis = {
            'Clouds':       u'\U00002601',
            'Clear':        u'\U00002600',
            'Rain':         u'\U0001F327',
            'Extreme':      u'\U0001F32A',
            'Snow':         u'\U0001F328',
            'Thunderstorm': u'\U000026C8',
            'Mist':         u'\U0001F32B',
            'Haze':         u'\U0001F324',
            'notsure':      u'\U0001F648'
    }

    return("".join([emojis[i] for i in emojis if weather_status == i]))

# ==== End of get_emoji function =============================================


def weather(bot, update, args):

    city = " ".join(args)
    username = update.message.from_user.username

    engine = create_engine(DATABASE)
    Base = automap_base()
    Base.prepare(engine, reflect=True)

    locations = Base.classes.locations

    if not city:
        with connector(engine) as ses:
            try:
                city = ses.query(locations.city).filter(
                    locations.username == username).one()
                city = "".join([i for i in city])
            except NoResultFound:
                try:
                    city = ses.query(locations.city).filter(
                        locations.username == "default_city").one()
                    city = "".join([i for i in city])
                except NoResultFound:
                    if username in ADMINS:
                        error_message = '''
                        You didn't set the default city
                        You can add default city by this command:
                        `/manage insert into locations(username,city) \
                        values(\"default_city\",\"YOUR CITY HERE\")`'''
                        error_message = "\n".join(
                            [i.strip() for i in error_message.split('\n')])
                    else:
                        error_message = "Administrator didn't set the default city\nTry /w City"
                    bot.send_message(chat_id=update.message.chat_id,
                                     parse_mode='markdown', text=error_message)
                    return

    try:
        owm = pyowm.OWM(WEATHER_TOKEN, language='en')
    except:
        error_message = "Invalid API token"
        bot.send_message(chat_id=update.message.chat_id, text=error_message)
        log_print('Weather "{0}"'.format(error_message), username)
        return

    try:
        observation = owm.weather_at_place(city)
    except pyowm.exceptions.not_found_error.NotFoundError:
        error_message = "Wrong location"
        bot.send_message(chat_id=update.message.chat_id, text=error_message)
        log_print('"{0}"'.format(error_message), username)
        return

    fc = owm.three_hours_forecast(city)
    w = observation.get_weather()
    city = observation.get_location().get_name()

    weathers, tomorrow = {}, {}

    # Today
    today = pyowm.timeutils.next_three_hours()
    weather = fc.get_weather_at(today)
    temp = str(round(weather.get_temperature(unit='celsius')["temp"]))
    if temp[0] != '-' and temp != "0":
        weathers["today", "temp", 0] = '+' + temp
    else:
        weathers["today", "temp", 0] = temp
    weathers["today", "emoji", 0] = get_emoji(weather.get_status())
    status = weather.get_detailed_status()
    weathers["today", "status", 0] = status[0].upper() + status[1:]

    # Tomorrow
    for i in range(6, 19, 6):
            weather = fc.get_weather_at(pyowm.timeutils.tomorrow(i, 0))
            temp = str(round(weather.get_temperature('celsius')["temp"]))
            if temp[0] != '-' and temp != "0":
                weathers["tomorrow", "temp", i] = '+' + temp
            else:
                weathers["tomorrow", "temp", i] = temp
            weathers["tomorrow", "emoji", i] = get_emoji(weather.get_status())
            status = weather.get_detailed_status()
            weathers["tomorrow", "status", i] = status[0].upper() + status[1:]

    now_temp = str(round(w.get_temperature(unit='celsius')["temp"]))
    if now_temp[0] != '-':
        now_temp = '+' + now_temp
    now_status = w.get_detailed_status()
    now_status = now_status[0].upper() + now_status[1:]
    now_emoji = get_emoji(w.get_status())

    try:
        message = ''.join("""
        *Now:*
        *{0}:* {1} {2} {3}

        *In near future:*
        {4} {5} {6}

        *Tomorrow:*
        *Morning:* {7} {8} {9}
        *Noon:* {10} {11} {12}
        *Evening:* {13} {14} {15}
        """.format(city,
                   now_temp,
                   now_emoji,
                   now_status,
                   *[weathers[i] for i in weathers]))
    except IndexError:
        error_message = "Something wrong with API:\n\n{}".format(weathers)
        bot.send_message(chat_id=update.message.chat_id, text=error_message)
        log_print('"{0}"'.format(error_message), username)
        return

    message = "\n".join([k.strip() for k in message.split('\n')])

    bot.send_message(chat_id=update.message.chat_id,
                     parse_mode="markdown", text=message)

    log_print('Weather "{0}"'.format(city), username)

# ==== End of weather function ===============================================


def wset(bot, update, args):

    city = " ".join(args)
    username = update.message.from_user.username

    engine = create_engine(DATABASE)
    Base = automap_base()
    Base.prepare(engine, reflect=True)

    locations = Base.classes.locations

    with connector(engine) as ses:
        try:
            ses.query(locations.username).filter(
                locations.username == username).one()
            if not city:
                w_city = "".join(ses.query(locations.city).filter(
                    locations.username == username).one())
                out_text = "@{0} city is {1}".format(username, w_city)
                city = 'deleted'
            elif city == "delete":
                ses.query(locations.username).filter(
                    locations.username == username).delete()
                out_text = "Deleted information about @{0}".format(username)
                city = 'deleted'
            else:
                ses.query(locations).filter(
                        locations.username == username).update({'city': city})
                out_text = "New city for @{0}: {1}".format(username, city)

        except NoResultFound:
            if not city or city == "delete":
                out_text = "No informaton about @{0}".format(username)
                city = 'none'
            else:
                new_location = locations(
                    username=username,
                    city=city)
                ses.add(new_location)
                out_text = "Added @{0}: {1}".format(username, city)

    bot.send_message(chat_id=update.message.chat_id, text=out_text)
    log_print('Wset "{0}"'.format(out_text))

# ==== End of wset function ===============================================


def random_content(bot, update, args):

    MAX_QUOTES = 5

    command = update.message.text.split()[0].replace('/', '')

    def keyboard_markup(i, count, arg):
        if i == count-1:
            keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("Another one!", callback_data='{}_1'.format(arg)),
                                              InlineKeyboardButton("I NEED MORE!", callback_data='{}_5'.format(arg))],
                                              [InlineKeyboardButton("No, thank you", callback_data='none')]])
        else:
            keyboard = InlineKeyboardMarkup([[]])
        return(keyboard)

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
            bot.send_message(chat_id=update.message.chat_id, text="```\n" +quote_id +
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


def parser(bot, update):

    in_text = update.message.text.lower().replace('ё', 'е').replace(',', '').replace('.', '')
    engine = create_engine(DATABASE)
    Base = automap_base()
    Base.prepare(engine, reflect=True)

    answers = Base.classes.answers
    w_phrases = Base.classes.w_phrases
    google_ignore = Base.classes.google_ignore
    google = Base.classes.google
    ping_phrases = Base.classes.ping_phrases
    ping_exclude = Base.classes.ping_exclude
    pingers = Base.classes.pingers

    # ------------ Weather ----------------
    with connector(engine) as ses:
        try:
            phrase = "".join(ses.query(w_phrases.match).filter(
                literal(in_text.lower()).contains(w_phrases.match)).one())
            weather(bot, update, in_text.lower()[in_text.lower().find(phrase)+len(phrase):].split())
            return
        except NoResultFound:
            pass

    # ------------ Google -----------------
    with conn(engine) as ses:
        g_in_text = in_text.replace("?", "")
        try:
            ses.query(google_ignore.ignore).filter(
                google_ignore.ignore.in_(g_in_text.split())).one()
        except NoResultFound:
            matches = ses.query(google.match).filter(
                literal(in_text).like(google.match + '%')).all()
            matches = [i for i in matches for i in i]
            if matches:
                g_in_text = g_in_text.replace(
                    sorted(matches, key=len)[-1], "").strip()

                if g_in_text:
                    out_text = 'https://www.google.ru/search?q={0}'.format(
                        g_in_text.replace(" ", "+"))
                    bot.send_message(chat_id=update.message.chat_id,
                                     disable_web_page_preview=1, text=out_text)
                    log_print('Google "{0}"'.format(g_in_text.strip()),
                               update.message.from_user.username)
                return

    # ------------ Ping -----------------
    with connector(engine) as ses:
        in_text_list = in_text.split()
        username = update.message.from_user.username
        chat_id = update.message.chat_id

        try:
            ses.query(ping_phrases.phrase).filter(
                ping_phrases.phrase.in_(in_text_list)).one()
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
                out_text = " ".join(["@" + i for i in usernames])
                bot.send_message(chat_id=update.message.chat_id, text=out_text)
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

def manage(bot, update, args):

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




# ==== End of manage function ================================================

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
            p_username = args[0]
            try:
                match = args[1].lower()
            except:
                if args[0] not in ["all","delete"]:
                    p_username = username
                    match = args[0]
            if not p_username: raise
        except:
            usage_text = "Usage: \n`/pinger username match`\n`/pinger all`\n`/pinger delete username match`"
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
                        out_text += "\n{} | {}".format(match.username, match.match)
                    bot.send_message(chat_id=update.message.chat_id,
                                     text=out_text)
                elif p_username == "delete":
                    try:
                        p_username = args[1]
                        try:
                            delete_match = args[2].lower()
                        except:
                            p_username = username
                            delete_match = args[1].lower()
                    except:
                        out_text = "Usage `/pinger delete username match`"
                        bot.send_message(chat_id=update.message.chat_id,
                                         parse_mode='markdown',
                                         text=out_text)
                        return
                    ses.query(pingers).filter(and_(
                           pingers.chat_id == chat_id,
                           pingers.username == p_username,
                           pingers.match == delete_match)).delete()
                    bot.send_message(chat_id=update.message.chat_id,
                                     text="Deleted")
                    log_print('Delete pinger "{0}"'.format(args_line), username)
                else:
                    with connector(engine) as ses:
                        new_pinger = pingers(
                            username=p_username,
                            match=match,
                            chat_id=chat_id)
                        ses.add(new_pinger)
                    bot.send_message(chat_id=update.message.chat_id,
                                     text="Successfuly added")
                    log_print('Added pinger "{0}"'.format(args_line), username)
            except:
                bot.send_message(chat_id=update.message.chat_id,
                                 text="There was some trouble")
                log_print('Error while add pinger "{0}"'.format(args_line), username)
    else:
        try:
            try:
                user_match = args[0].lower()
                if not user_match: raise
            except:
                out_text = "Usage: \n`/pinger match`\n`/pinger all`\n`/pinger delete match`"
                bot.send_message(chat_id=update.message.chat_id,
                                 parse_mode='markdown',
                                 text=out_text)
                return
            with connector(engine) as ses:
                if user_match == "all":
                    all_matches = ses.query(pingers).filter(and_(
                                  pingers.chat_id == chat_id,
                                  pingers.username == username)).all()
                    out_text = ""
                    for match in all_matches:
                        out_text += "\n{} | {}".format(match.username, match.match)
                    bot.send_message(chat_id=update.message.chat_id,
                                     text=out_text)
                elif user_match == "delete":
                    try:
                        delete_match = args[1].lower()
                    except:
                        out_text = "Usage `/pinger delete match`"
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
                                         text="Successfuly added")
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


def cmd(bot, update, args):

    username = update.message.from_user.username
    if username not in ADMINS:
        bot.send_message(chat_id=update.message.chat_id,
                         text="You are not allowed to use this command")
        log_print('Try of command', username)
        return
    else:
        if not args:
            bot.send_message(chat_id=update.message.chat_id,
                             text="Usage `/cmd command`",
                             parse_mode='markdown')
            log_print('Usage of command', username)
            return
        else:
            output = ['','']
            try:
                process = subprocess.Popen(args, stdout=subprocess.PIPE)
                output = list(process.communicate())
            except FileNotFoundError:
                output[0] = b'\n'
                output[1] = b'No such command\n'
            for i in range(len(output)):
                try:
                    output[i] = output[i].decode("utf-8")
                except AttributeError:
                    output[i] = ""
            bot.send_message(chat_id=update.message.chat_id,
                             text="*Output:*\n```\n{0}```*Errors:*\n```\n{1}```".format(*output),
                             parse_mode='markdown')
            log_print('Command "{0}"'.format(" ".join(args)), username)

# ==== End of cmd function ===================================================


def create_table():

    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY

    try:
        db_check_file = os.open(DATABASE_HOST, flags)
    except OSError as e:
        if e.errno == errno.EEXIST:
            pass
        else:
            raise
    else:
        os.fdopen(db_check_file, 'w')

    engine = create_engine(DATABASE)
    metadata = MetaData(engine)

    pingers = Table('pingers', metadata,
                    Column('id', Integer, primary_key=True, autoincrement=True),
                    Column('username', Unicode(255)),
                    Column('chat_id', Unicode(255)),
                    Column('match', Unicode(255)))

    ping_phrases = Table('ping_phrases', metadata,
                         Column('phrase', Unicode(255), primary_key=True))

    google_ignore = Table('google_ignore', metadata,
                          Column('ignore', Unicode(255), primary_key=True))

    google = Table('google', metadata,
                   Column('match', Unicode(255), primary_key=True))

    locations = Table('locations', metadata,
                      Column('username', Unicode(255), primary_key=True),
                      Column('city', Unicode(255)))

    w_phrases = Table('w_phrases', metadata,
                      Column('match', Unicode(255), primary_key=True))

    answers = Table('answers', metadata,
                    Column('match', Unicode(255), primary_key=True),
                    Column('string', Unicode(255)))

    ping_exclude = Table('ping_exclude', metadata,
                         Column('match', Unicode(255), primary_key=True))

    metadata.create_all()

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
        random_content(bot,query,[value])

# ==== End of buttons function ===============================================


def log_print(message, *username):
    timestamp = datetime.now(tzlocal()).strftime("[%d/%b/%Y:%H:%M:%S %z]")
    if not username:
        print("{0}: {1}".format(timestamp, message))
    else:
        print("{0}: {1} by @{2}".format(timestamp, message, "".join(username)))


@contextmanager
def connector(engine):
    session = Session(engine)
    try:
        yield session
        session.commit()
    except:
        error = str(sys.exc_info())
        print("Error is: ", error)
        session.rollback()
        raise
    finally:
        session.close()

# ============================================================================


log_print('Started')

try:
    create_table()

    updater = Updater(token=BOT_TOKEN)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler(['start', 'info'], start))
    dispatcher.add_handler(CommandHandler(['weather', 'w'], weather, pass_args=True))
    dispatcher.add_handler(CommandHandler(['ibash', 'loglist', 'cat', 'dog'], random_content, pass_args=True))
    dispatcher.add_handler(CommandHandler('cmd', cmd, pass_args=True))
    dispatcher.add_handler(CommandHandler('wset', wset, pass_args=True))
    dispatcher.add_handler(CommandHandler('manage', manage, pass_args=True))
    dispatcher.add_handler(CommandHandler('pinger', pinger, pass_args=True))
    dispatcher.add_handler(CallbackQueryHandler(buttons))
    dispatcher.add_handler(MessageHandler(Filters.text, parser))

    if MODE.lower() == 'webhook':
        updater.start_webhook(listen="0.0.0.0",
                              port=WEBHOOK_PORT,
                              url_path=BOT_TOKEN)
        updater.bot.set_webhook(WEBHOOK_URL)
        updater.idle()
    else:
        updater.start_polling()
except sqlite3.ProgrammingError:
    pass

# vim: set fdm=marker:

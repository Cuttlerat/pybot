#!/usr/bin/env python3

# Import {{{
import json
import requests
import pytz 
import sqlite3
import logging
import os
import sys
import errno

from bs4 import BeautifulSoup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from contextlib import contextmanager
from datetime import datetime
from sqlalchemy import *
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.exc import ResourceClosedError
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import NoResultFound
from dateutil.tz import tzlocal
from tokens import *
# }}}

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

DATABASE ='sqlite:///{}'.format(DATABASE_HOST) 

#===========FUNCTIONS========================================================

def start(bot, update):

    start_text = '''
    This is my first bot on Python.
    You can see the code here https://github.com/Cuttlerat/pybot
    by @Cuttlerat
    '''
    start_text = "\n".join([ i.strip() for i in start_text.split('\n') ])
    bot.send_message(chat_id=update.message.chat_id, text = start_text)

#==== End of start function =================================================

def get_emoji(emoji_code):

    emojis = {
        '☀️':  [113],         # Sunny
        '⛅️': [116],         # Partly cloudy
        '🌥': [119],         # Cloudy
        '☁️':  [122],         # Overcast
        '🌩': [200],         # Thunder
        '🌫': [143,248,260], # Fog
        '🌦': [176,263,266,281,293,296,299,302,311,317,353,362],                 # Light Rain
        '🌨': [179,182,185,227,230,323,326,329,332,335,338,350,368,371,374,377], # Snow
        '🌧': [284,305,308,314,320,356,359,365],                                 # Heavy rain
        '⛈':  [386,389,392,395]                                                  # Rain with thunder
        }

    return("".join([i for i in emojis if emoji_code in [x for x in emojis[i]]]))

#==== End of get_emoji function =============================================

def weather(bot, update, args):

    city = "".join(args)
    username = update.message.from_user.username

    engine = create_engine(DATABASE)
    Base = automap_base()
    Base.prepare(engine, reflect=True)

    locations = Base.classes.locations

    if not city:
        with conn(engine) as ses:
            try:
                city = ses.query(locations.city).filter(locations.username == username).one()
                city = [ i for i in city ]
            except NoResultFound:
                try:
                    city = ses.query(locations.city).filter(locations.username == "default_city").one()
                    city = [ i for i in city ]
                except NoResultFound:
                    if username in ADMINS:
                        error_message = '''You didn't set the default city
                                           You can add default city by this command:
                                           `/manage insert into locations(username,city) values(\"default_city\",\"YOUR CITY HERE\")`'''
                        error_message = "\n".join([ i.strip() for i in error_message.split('\n') ])
                    else:
                        error_message = "Administrator didn't set the default city\nTry /w City"
                    bot.send_message(chat_id=update.message.chat_id, parse_mode = 'markdown', text = error_message )
                    return

    w_params = {        'q': city, 
                      'key': WEATHER_TOKEN, 
                   'format': 'json', 
                     'date': 'today', 
                     'fx24': 'yes', 
                     'lang': 'ru'            }

    weather_api_bug = False

    now_city = ""
    while not now_city or now_city == "null":

        w_response = requests.get('https://api.worldweatheronline.com/premium/v1/weather.ashx', w_params).json()
        try:
            now_city  = w_response["data"]["request"][0]["query"]
        except (KeyError, json.decoder.JSONDecodeError):
            now_city = ""
        if (not now_city or now_city == "null") and weather_api_bug: break
        if (not now_city or now_city == "null"): weather_api_bug = True

    try:
        now_temp  = w_response["data"]["current_condition"][0]["temp_C"]
        if now_temp[0] != '-': now_temp = '+' + now_temp
    except (KeyError, json.decoder.JSONDecodeError):
        error_message='Wrong location!'

        bot.send_message(chat_id=update.message.chat_id, text = error_message )

        log_dict = {'timestamp': log_timestamp(), 
                'error_message': "Wrong location", 
                     'username': update.message.from_user.username }
        print("{timestamp}: \"{error_message}\" by @{username}".format(**log_dict))
        return


    now_comment = w_response["data"]["current_condition"][0]["lang_ru"][0]["value"]

    now_time  = datetime.strptime(w_response["data"]["current_condition"][0]["observation_time"] + " 2017", '%I:%M %p %Y')
    now_time  = pytz.timezone('Europe/Moscow').fromutc(now_time)
    now_time  = "{:%H:%M}".format(now_time)
    now_emoji = get_emoji(int(w_response["data"]["current_condition"][0]["weatherCode"]))

    weather = {}
    for j in range(2):
        for i in range(3):
            weather[j,"temp",i]    = w_response["data"]["weather"][j]["hourly"][2+(i*3)]["tempC"]
            if weather[j,"temp",i][0] != '-': weather[j,"temp",i] = '+' + weather[j,"temp",i]
            weather[j,"emoji",i]   = get_emoji(int(w_response["data"]["weather"][j]["hourly"][2+(i*3)]["weatherCode"]))
            weather[j,"comment",i] = w_response["data"]["weather"][j]["hourly"][2+(i*3)]["lang_ru"][0]["value"]
    
    message = ''.join("""
    *Now:* 
    *[{0}]:* {1} {2} {3}
    {4}

    *Today:*
    *Morning:* {5} {6} {7}
    *Noon:* {8} {9} {10}
    *Evening:* {11} {12} {13}

    *Tommorow:* 
    *Morning:* {14} {15} {16}
    *Noon:* {17} {18} {19}
    *Evening:* {20} {21} {22}
    """.format(now_time,
               now_temp,
               now_emoji,
               now_comment,
               now_city,
               *[ weather[i] for i in weather ] ))
   
    message = "\n".join([ k.strip() for k in message.split('\n') ])
    
    bot.send_message(chat_id=update.message.chat_id, parse_mode = "markdown", text = message )

    # LOG
    log_dict = {'timestamp': log_timestamp(), 
                  'message': "Weather {0}".format(now_city), 
                 'username': update.message.from_user.username }
    print("{timestamp}: \"{message}\" by @{username}".format(**log_dict))

#==== End of weather function ===============================================

def wset(bot, update, args):

    city = "".join(args)
    username = update.message.from_user.username

    engine = create_engine(DATABASE)
    Base = automap_base()
    Base.prepare(engine, reflect=True)

    locations = Base.classes.locations

    with conn(engine) as ses:
        try:
            ses.query(locations.username).filter(locations.username == username).one()
            if not city or city == "delete":
                ses.query(locations.username).filter(locations.username == username).delete()
                out_text = "Deleted information about @{0}".format(username)
                city = 'deleted'
            else:
                ses.query(locations.username).update(locations.username == username)
                out_text = "New city for @{0}: {1}".format(username,city)

        except NoResultFound:
            if not city or city == "delete":
                out_text = "No informaton about @{0}".format(update.message.from_user.username)
                city = 'none'
            else:
                new_location = locations(
                    username = username,
                    city = city)
                ses.add(new_location)
                out_text = "Added @{0}: {1}".format(update.message.from_user.username,city)

    bot.send_message( chat_id = update.message.chat_id, text = out_text )
    log_dict = {'timestamp': log_timestamp(), 
                     'city': city, 
                 'username': update.message.from_user.username }
    print("{timestamp}: wset {city} by @{username}".format(**log_dict))


def ibash(bot, update, args):

    count = int(''.join(args)) if ''.join(args).isdigit() else 1
    if count > 5: count = 5

    for i in range(count):
        i_response = requests.get('http://ibash.org.ru/random.php').text
        soup = BeautifulSoup(i_response, "html.parser")
        
        quote_id = soup.find_all("div", class_="quote")[0].a.get_text()
        for br in soup.find_all("br"): 
            br.replace_with("\n")
        quote_text = soup.find("div", class_="quotbody").text
        bot.send_message(chat_id = update.message.chat_id, text = quote_id+"\n"+quote_text+"\n", disable_web_page_preview = 1)

    # LOG
    log_dict = {'timestamp': log_timestamp(), 
                    'count': count, 
                 'username': update.message.from_user.username }
    print("{timestamp}: ibash {count} by @{username}".format(**log_dict))

#==== End of ibash function =================================================

def loglist(bot, update, args):

    #TODO Merge into one function with ibash
    #     I need help with getting a what command was in message inside function to do that
    count = int(''.join(args)) if ''.join(args).isdigit() else 1
    if count > 5: count = 5

    for i in range(count):
        l_raw_json = json.loads(requests.get('https://loglist.net/api/quote/random').text)
        quote_id   = l_raw_json['id']
        quote_text = l_raw_json['content']
        bot.send_message(chat_id = update.message.chat_id, text = "#"+quote_id+"\n"+quote_text+"\n", disable_web_page_preview = 1)

    log_dict = {'timestamp': log_timestamp(), 
                    'count': count, 
                 'username': update.message.from_user.username }
    print("{timestamp}: loglist {count} by @{username}".format(**log_dict))

#==== End of loglist function ===============================================

def parser(bot, update):

    in_text = update.message.text.lower().replace('ё','е')
    engine = create_engine(DATABASE)
    Base = automap_base()
    Base.prepare(engine, reflect=True)

    answers = Base.classes.answers
    google_ignore = Base.classes.google_ignore
    google = Base.classes.google
    ping_phrases = Base.classes.ping_phrases
    ping_exclude = Base.classes.ping_exclude
    pingers = Base.classes.pingers

    # ------------ Google ----------------- 

    with conn(engine) as ses:
       try:
          ses.query(google_ignore.ignore).filter(literal(in_text).contains(google_ignore.ignore)).one()
       except NoResultFound:
            g_in_text = in_text.replace(",","").replace(".","")
            matches = ses.query(google.match).filter(literal(g_in_text).contains(google.match)).all()
            matches = [i for i in matches for i in i]
            if matches:
                g_in_text = g_in_text.replace(sorted(matches, key=len)[-1],"").strip()
                
                if g_in_text:
                    out_text = 'https://www.google.ru/search?q={0}'.format(g_in_text.replace(" ","+"))
                    bot.send_message( chat_id = update.message.chat_id, disable_web_page_preview = 1, text = out_text )
                    log_dict = {'timestamp': log_timestamp(), 
                                   'google': g_in_text.strip(),
                                 'username': update.message.from_user.username }
                    print('{timestamp}: Google "{google}" by @{username}'.format(**log_dict))
                return

    # ------------ Ping ----------------- 

    with conn(engine) as ses:
        chat_id = update.message.chat_id
        try:
            ses.query(ping_phrases.phrase).filter(literal(in_text).contains(ping_phrases.phrase)).one()
        except NoResultFound:
            return
        usernames = ses.query(pingers.username).filter(
                and_(
                literal(in_text).contains(pingers.match),
                or_(
                    pingers.chat_id == chat_id,
                    pingers.chat_id == "all")
                )).distinct().all()
        usernames = [i for i in usernames for i in i]
        if 'EVERYONE GET IN HERE' in usernames:
            try:
                ses.query(ping_exclude.match).filter(literal(in_text).contains(ping_exclude.match)).one()
                usernames = ses.query(pingers.username).filter(
                        and_(
                        pingers.username.notin_(usernames),
                        or_(
                            pingers.chat_id == chat_id,
                            pingers.chat_id == "all")
                        )).distinct().all()
                usernames = [ i for i in usernames for i in i ]

            except NoResultFound:
                usernames = ses.query(pingers.username).filter(
                        and_(
                        pingers.username != 'EVERYONE GET IN HERE',
                        or_(
                            pingers.chat_id == chat_id,
                            pingers.chat_id == "all")
                        )).distinct().all()
                usernames = [i for i in usernames for i in i ]

        if usernames:
            out_text = " ".join([ "@"+i for i in usernames ])
            bot.send_message( chat_id = update.message.chat_id, text = out_text )
            log_dict = {'timestamp': log_timestamp(), 
                          'pingers': out_text, 
                         'username': update.message.from_user.username }
            print('{timestamp}: ping "{pingers}" by @{username}'.format(**log_dict))

    # ------------ Answer ----------------- 

    with conn(engine) as ses:
       out_text = ses.query(answers.string).filter(literal(in_text).contains(answers.match))
    for message in ["".join(i) for i in out_text]:
        bot.send_message( chat_id = update.message.chat_id, text = message )
        log_dict = {'timestamp': log_timestamp(), 
                     'username': update.message.from_user.username }
        print("{timestamp}: Answer by @{username}".format(**log_dict))


#==== End of parser function ================================================

def manage(bot, update, args):

    if not update.message.from_user.username in ADMINS:
        out_text = "You are not an administrator. The incident will be reported"
        commans = "not an administrator"
    else:
        command = " ".join(args)

        if command == ".schema": command = "SELECT sql FROM sqlite_master WHERE type = 'table'"
        if command == ".tables": command = "SELECT name FROM sqlite_master WHERE type = 'table'"
        if "%%%chat_id%%%" in command: command = command.replace("%%%chat_id%%%", str(update.message.chat_id))

        engine = create_engine(DATABASE)
        conn = engine.connect()

        try:
            out_text = "\n".join([" | ".join([str(i) for i in i]) for i in engine.execute(command).fetchall()])
            conn.close()
        except ResourceClosedError:
            out_text = command = "Successfuly"
            conn.close()
        except:
            out_text = command = "Bad command"
            conn.close()

    if out_text:
        bot.send_message( chat_id = update.message.chat_id, text = out_text )
        log_dict = {'timestamp': log_timestamp(), 
                      'command': command, 
                     'username': update.message.from_user.username }
        print('{timestamp}: Manage "{command}" by @{username}'.format(**log_dict))


#==== End of manage function ================================================

def pinger(bot,update,args):

    if update.message.from_user.username in ADMINS:
        chat_id = update.message.chat_id
        command = " ".join(args).split(' ')
        username = command[0]
        match = " ".join(command[1:])

        engine = create_engine(DATABASE)
        Base = automap_base()
        Base.prepare(engine, reflect=True)
        pingers = Base.classes.pingers

        try:
            with conn(engine) as ses:
                new_pinger = pingers(
                    username = username,
                    match = match,
                    chat_id = chat_id)
                ses.add(new_pinger)
            bot.send_message( chat_id = update.message.chat_id, text = "Successfuly added" )
            log_dict = {'timestamp': log_timestamp(), 
                          'command': " ".join(command), 
                         'username': update.message.from_user.username }
            print('{timestamp}: Added pinger "{command}" by @{username}'.format(**log_dict))
        except:
            bot.send_message( chat_id = update.message.chat_id, text = "There was some trouble" )
            log_dict = {'timestamp': log_timestamp(), 
                          'command': " ".join(command), 
                         'username': update.message.from_user.username }
            print('{timestamp}: Error while add pinger "{command}" by @{username}'.format(**log_dict))
    else:
        bot.send_message( chat_id = update.message.chat_id, text = "You are not an administrator" )
        log_dict = {'timestamp': log_timestamp(), 
                     'username': update.message.from_user.username }
        print('{timestamp}: Trying to pinger by @{username}'.format(**log_dict))

#==== End of pinger function ================================================

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
            Column('id', Integer, primary_key = True, autoincrement = True),
            Column('username', Unicode(255)),
            Column('chat_id', Unicode(255)),
            Column('match', Unicode(255)))

    ping_phrases = Table('ping_phrases', metadata,
            Column('phrase', Unicode(255), primary_key = True))

    google_ignore = Table('google_ignore', metadata,
            Column('ignore', Unicode(255), primary_key = True))

    google = Table('google', metadata,
            Column('match', Unicode(255), primary_key = True))

    locations = Table('locations', metadata,
            Column('username', Unicode(255), primary_key = True),
            Column('city', Unicode(255)))

    answers = Table('answers', metadata,
            Column('match', Unicode(255), primary_key = True),
            Column('string', Unicode(255)))

    ping_exclude = Table('ping_exclude', metadata,
            Column('match', Unicode(255), primary_key = True))

    metadata.create_all()

def log_timestamp():
    return(datetime.now(tzlocal()).strftime("[%d/%b/%Y:%H:%M:%S %z]"))

@contextmanager
def conn(engine):
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

#============================================================================

print('{}: Started'.format(log_timestamp()))

create_table()

updater    = Updater(token=BOT_TOKEN)
dispatcher = updater.dispatcher

dispatcher.add_handler(CommandHandler('start', start))
dispatcher.add_handler(CommandHandler('info', start))
dispatcher.add_handler(CommandHandler('weather', weather, pass_args=True))
dispatcher.add_handler(CommandHandler('w', weather, pass_args=True))
dispatcher.add_handler(CommandHandler('wset', wset, pass_args=True))
dispatcher.add_handler(CommandHandler('ibash', ibash, pass_args=True))
dispatcher.add_handler(CommandHandler('loglist', loglist, pass_args=True))
dispatcher.add_handler(CommandHandler('manage', manage, pass_args=True))
dispatcher.add_handler(CommandHandler('pinger', pinger, pass_args=True))
dispatcher.add_handler(MessageHandler(Filters.text, parser))

updater.start_polling()

# vim: set fdm=marker:

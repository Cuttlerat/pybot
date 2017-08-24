#!/usr/bin/env python3
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
from sqlalchemy.orm import Session
from dateutil.tz import tzlocal
from tokens import *

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

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

    conn = sqlite3.connect(DATABASE)
    db = conn.cursor()

    try:
        db_check = db.execute('''
        SELECT EXISTS(SELECT 1 FROM locations WHERE "{0}" LIKE locations.username) LIMIT 1
        '''.format(update.message.from_user.username)).fetchone()
        if 1 in db_check and not args:
            city = ''.join(db.execute('''
            SELECT city FROM locations WHERE "{0}" LIKE locations.username
            '''.format(update.message.from_user.username)).fetchone())
        else:
            city = ' '.join(args) if args else ''.join(db.execute('''
                                                SELECT city FROM locations WHERE username="default_city"
                                                ''').fetchone())
    except:
        if update.message.from_user.username in ADMINS:
            error_message = '''You didn't set the default city
                               You can add default city by this command:
                               `/manage insert into locations(username,city) values(\"default_city\",\"YOUR CITY HERE\")`'''
            error_message = "\n".join([ i.strip() for i in error_message.split('\n') ])
        else:
            error_message = "Administrator didn't set the default city\nTry /w City"
        bot.send_message(chat_id=update.message.chat_id, parse_mode = 'markdown', text = error_message )

        # LOG
        log_dict = {'timestamp': log_timestamp(), 
                'error_message': "Wrong location", 
                     'username': update.message.from_user.username }
        print("{timestamp}: \"{error_message}\" by @{username}".format(**log_dict))
        conn.commit()
        db.close()
        conn.close()
        return

    conn.commit()
    db.close()
    conn.close()

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

        # LOG
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
    conn = sqlite3.connect(DATABASE)
    db = conn.cursor()

    db_check = db.execute('''
    SELECT EXISTS(SELECT 1 FROM locations WHERE "{0}" LIKE locations.username) LIMIT 1
    '''.format(update.message.from_user.username)).fetchone()

    if 1 in db_check:
        if not city or city == "delete":
            db.execute('''
            DELETE FROM locations WHERE "{0}" LIKE locations.username
            '''.format(update.message.from_user.username))
            out_text = "Deleted information about @{0}".format(update.message.from_user.username)
            city = 'deleted'
        else:
            db.execute('''
            UPDATE locations SET city="{1}" WHERE username="{0}"
            '''.format(update.message.from_user.username, city))
            out_text = "New city for @{0}: {1}".format(update.message.from_user.username,city)
    else:
        if not city or "delete" in city:
            out_text = "No informaton about @{0}".format(update.message.from_user.username)
            city = 'none'
        else:
            db.execute('''
            INSERT INTO locations(username, city) VALUES("{0}","{1}")
            '''.format(update.message.from_user.username,city))
            out_text = "Added @{0}: {1}".format(update.message.from_user.username,city)

    conn.commit()
    db.close()
    conn.close()

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

    # LOG
    log_dict = {'timestamp': log_timestamp(), 
                    'count': count, 
                 'username': update.message.from_user.username }
    print("{timestamp}: loglist {count} by @{username}".format(**log_dict))

#==== End of loglist function ===============================================

def parser(bot, update):

    in_text = update.message.text.lower().replace('ё','е')
    conn = sqlite3.connect(DATABASE)

    # ------------ Google ----------------- 
    try:
        g_conn = sqlite3.connect(DATABASE)
        g_db = g_conn.cursor()
        out_text = ""

        gi_db_check = g_db.execute('''
        SELECT EXISTS(SELECT 1 FROM google_ignore WHERE "{0}" LIKE '%'||google_ignore.ignore||'%') LIMIT 1
        '''.format(in_text)).fetchone()

        if 0 in gi_db_check:
            g_in_text = in_text.replace(",","").replace(".","")
            g_db_check = g_db.execute('''
            SELECT EXISTS(SELECT 1 FROM google WHERE "{0}" LIKE '%'||google.match||'%') LIMIT 1
            '''.format(g_in_text)).fetchone()
            if 1 in g_db_check:
                matches = [ i for i in g_db.execute('''
                    SELECT * FROM google WHERE "{0}" LIKE '%'||google.match||'%' 
                    '''.format(g_in_text)).fetchall() for i in i ]

                g_conn.commit()
                g_db.close()
                g_conn.close()

                g_in_text = g_in_text.replace(sorted(matches, key=len)[-1],"")
                
                out_text = 'https://www.google.ru/search?q={0}'.format(g_in_text.strip().replace(" ","+"))

                if out_text:
                    bot.send_message( chat_id = update.message.chat_id, disable_web_page_preview = 1, text = out_text )
                    log_dict = {'timestamp': log_timestamp(), 
                                   'google': g_in_text.strip(),
                                 'username': update.message.from_user.username }
                    print('{timestamp}: Google "{google}" by @{username}'.format(**log_dict))
                    return
    except:
        try:
            g_conn.commit()
            g_db.close()
            g_conn.close()
        except:
            return
        return

    # ------------ Ping ----------------- 
    try:
        chat_id = update.message.chat_id
        db = conn.cursor()
        out_text = ""
        db_check = db.execute('''
        SELECT EXISTS(SELECT 1 FROM ping_phrases WHERE "{0}" LIKE '%'||ping_phrases.phrase||'%') LIMIT 1
        '''.format(in_text)).fetchone()

        if 1 in db_check:
            out_text = " ".join([ i for i in db.execute('''
                SELECT DISTINCT username FROM pingers WHERE "{0}" LIKE '%'||pingers.match||'%' AND ("{1}" == chat_id OR chat_id == "all")
                '''.format(in_text, chat_id)).fetchall() for i in i ])
            if 'EVERYONE GET IN HERE' in out_text:
                pingers_check = db.execute('''
                    SELECT EXISTS(SELECT 1 FROM ping_exclude WHERE "{0}" LIKE '%'||ping_exclude.match||'%') LIMIT 1
                    '''.format(in_text)).fetchone()
                if 1 in pingers_check:
                    out_text = " ".join([ i for i in db.execute('''
                    SELECT DISTINCT username FROM pingers WHERE "{0} {1}" NOT LIKE '%'||username||'%' AND ("{2}" == chat_id OR chat_id == "all")
                    '''.format(update.message.from_user.username, out_text, chat_id)).fetchall() for i in i ])
                else:
                    out_text = " ".join([ i for i in db.execute('''
                    SELECT DISTINCT username FROM pingers WHERE pingers.username 
                    NOT LIKE "EVERYONE GET IN HERE" AND pingers.username NOT LIKE "{0}" AND ("{1}" == chat_id OR chat_id == "all")
                    '''.format(update.message.from_user.username, chat_id)).fetchall() for i in i ])

        conn.commit()
        db.close()
        conn.close()

        if out_text:
            out_text = " ".join([ "@"+i for i in out_text.split(' ') ])
            bot.send_message( chat_id = update.message.chat_id, text = out_text )
            log_dict = {'timestamp': log_timestamp(), 
                          'pingers': out_text, 
                         'username': update.message.from_user.username }
            print("{timestamp}: ping {pingers} by @{username}".format(**log_dict))
    except:
        conn.commit()
        db.close()
        conn.close()
        return
    # ------------ Answer ----------------- 
    try:
        a_conn = sqlite3.connect(DATABASE)
        a_db = a_conn.cursor()
        out_text = ""

        a_db_check = a_db.execute('''
        SELECT EXISTS(SELECT 1 FROM answers WHERE "{0}" LIKE '%'||answers.match||'%') LIMIT 1
        '''.format(in_text)).fetchone()

        if 1 in a_db_check:
            out_text = [ i for i in a_db.execute('''
                SELECT string FROM answers WHERE "{0}" LIKE '%'||answers.match||'%' 
                '''.format(in_text)).fetchall() for i in i ]

        a_conn.commit()
        a_db.close()
        a_conn.close()

        for message in out_text:
            bot.send_message( chat_id = update.message.chat_id, text = message )
            log_dict = {'timestamp': log_timestamp(), 
                         'username': update.message.from_user.username }
            print("{timestamp}: Answer by @{username}".format(**log_dict))
    except:
        a_conn.commit()
        a_db.close()
        a_conn.close()
        return


#==== End of parser function ================================================

def manage(bot, update, args):

    if not update.message.from_user.username in ADMINS:
        out_text = "You are not an administrator. The incident will be reported"
        commans = "not an administrator"
    else:
        command = " ".join(args)

        if command == ".schema": command = "SELECT sql FROM sqlite_master WHERE type = 'table'"
        if command == ".tables": command = "SELECT name FROM sqlite_master WHERE type = 'table'"
        if "%%%chat_id%%%" in command: command = command.replace("%chat_id%", str(update.message.chat_id))

        engine = create_engine('sqlite:///{}'.format(DATABASE))
        conn = engine.connect()

        try:
            out_text = "\n".join([" | ".join([str(i) for i in i]) for i in engine.execute(command).fetchall()])
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

        engine = create_engine('sqlite:///{}'.format(DATABASE))
        conn = engine.connect()
        metadata = MetaData(bind = engine, reflect = True)
        pingers = metadata.tables['pingers']

        try:
            conn.execute(pingers.insert().values(
                username = username,
                match = match,
                chat_id = chat_id))
            bot.send_message( chat_id = update.message.chat_id, text = "Successfuly added" )
            log_dict = {'timestamp': log_timestamp(), 
                          'command': " ".join(command), 
                         'username': update.message.from_user.username }
            print('{timestamp}: Added pinger "{command}" by @{username}'.format(**log_dict))
            conn.close()
        except:
            bot.send_message( chat_id = update.message.chat_id, text = "There was some trouble" )
            log_dict = {'timestamp': log_timestamp(), 
                          'command': " ".join(command), 
                         'username': update.message.from_user.username }
            print('{timestamp}: Error while add pinger "{command}" by @{username}'.format(**log_dict))
            conn.close()
    else:
        bot.send_message( chat_id = update.message.chat_id, text = "You are not an administrator" )
        log_dict = {'timestamp': log_timestamp(), 
                     'username': update.message.from_user.username }
        print('{timestamp}: Trying to pinger by @{username}'.format(**log_dict))

#==== End of pinger function ================================================

def test(bot,update,args):

    engine = create_engine('sqlite:///{}'.format(DATABASE))
    Base = automap_base()
    Base.prepare(engine, reflect=True)
    pingers = Base.classes.pingers

    with conn(engine) as ses:
        res = ses.query(pingers.username)
        
    bot.send_message( chat_id = update.message.chat_id, text = "\n".join([i for i in res for i in i]) )
    

def create_table():

    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY

    try:
        db_check_file = os.open(DATABASE, flags)
    except OSError as e:
        if e.errno == errno.EEXIST: 
            pass
        else: 
            raise
    else:  
        os.fdopen(db_check_file, 'w')

    engine = create_engine('sqlite:///{}'.format(DATABASE))
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
dispatcher.add_handler(CommandHandler('test', test, pass_args=True))
dispatcher.add_handler(MessageHandler(Filters.text, parser))

updater.start_polling()

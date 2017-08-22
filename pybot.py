#!/usr/bin/env python3
import json
import requests
import pytz 
import sqlite3
import logging

from bs4 import BeautifulSoup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from datetime import datetime
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

    emoji_code = str(emoji_code)

    # Sunny
    if "113" in emoji_code:
        emoji_code = emoji_code.replace("113","☀️")

    # Partly cloudy
    if "116" in emoji_code:
        emoji_code = emoji_code.replace("116","🌥")

    # Cloudy
    if "119" in emoji_code:
        emoji_code = emoji_code.replace("119","🌥")

    # Overcast
    if "122" in emoji_code:
        emoji_code = emoji_code.replace("122","☁️")

    # Thunder
    if "200" in emoji_code:
        emoji_code = emoji_code.replace("200","🌩")

    # Fog
    for i in ["143","248","260"]:
        if i in emoji_code:
            emoji_code = emoji_code.replace(i,"🌫")

    # Light Rain
    for i in ["176","263","266","281","293","296","299","302","311","317","362"]:
        if i in emoji_code:
            emoji_code = emoji_code.replace(i,"🌧")

    # Show
    for i in ["179","182","185","227","230","323","326","329","332","335","338","350","353","368","371","374","377"]:
        if i in emoji_code:
            emoji_code = emoji_code.replace(i,"🌨")

    # Heavy rain
    for i in ["284","305","308","314","320","356","359","365"]:
        if i in emoji_code:
            emoji_code = emoji_code.replace(i,"🌧")

    # Rain with thunder
    for i in ["386","389","392","395"]:
        if i in emoji_code:
            emoji_code = emoji_code.replace(i,"⛈")

    return(emoji_code)

#==== End of get_emoji function =============================================

def weather(bot, update, args):

    conn = sqlite3.connect('data/pybot.db')
    db = conn.cursor()

    db_check = db.execute('''
    SELECT EXISTS(SELECT 1 FROM locations WHERE "{0}" LIKE locations.username) LIMIT 1
    '''.format(update.message.from_user.username)).fetchone()

    if 1 in db_check:
        city = ''.join(db.execute('''
        SELECT city FROM locations WHERE "{0}" LIKE locations.username
        '''.format(update.message.from_user.username)).fetchone())
    else:
        city = ' '.join(args) if args else ''.join(db.execute('''
                                            SELECT city FROM locations WHERE username="default_city"
                                            ''').fetchone())

    conn.commit()
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
        except KeyError:
            now_city = ""
        if not (now_city or now_city == "null") and weather_api_bug: break
        if not (now_city or now_city == "null"): weather_api_bug = True

    try:
        now_temp  = w_response["data"]["current_condition"][0]["temp_C"]
    except KeyError:
        error_message='Wrong location!'

        bot.send_message(chat_id=update.message.chat_id, text = error_message )

        # LOG
        log_dict = {'timestamp': log_timestamp(), 
                'error_message': "Wrong location", 
                     'username': update.message.from_user.username }
        print("{timestamp}: \"{error_message}\" by @{username}".format(**log_dict))

    if now_temp[0] != '-': now_temp = '+' + now_temp

    now_comment = w_response["data"]["current_condition"][0]["lang_ru"][0]["value"]

    now_time  = datetime.strptime(w_response["data"]["current_condition"][0]["observation_time"] + " 2017", '%I:%M %p %Y')
    now_time  = pytz.timezone('Europe/Moscow').fromutc(now_time)
    now_time  = "{:%H:%M}".format(now_time)
    now_emoji = get_emoji(w_response["data"]["current_condition"][0]["weatherCode"])

    weather = {}
    for j in range(2):
        for i in range(3):
            weather[j,"temp",i]    = w_response["data"]["weather"][j]["hourly"][2+(i*3)]["tempC"]
            if weather[j,"temp",i][0] != '-': weather[j,"temp",i] = '+' + weather[j,"temp",i]
            weather[j,"emoji",i]   = get_emoji(w_response["data"]["weather"][j]["hourly"][2+(i*3)]["weatherCode"])
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
    conn = sqlite3.connect('data/pybot.db')
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
            INSERT INTO locations(username,city) VALUES("{0}","{1}")
            '''.format(update.message.from_user.username,city))
            out_text = "Added @{0}: {1}".format(update.message.from_user.username,city)

    conn.commit()
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
    conn = sqlite3.connect('data/pybot.db')
    db = conn.cursor()

    db_check = db.execute('''
    SELECT EXISTS(SELECT 1 FROM ping_phrases WHERE "{0}" LIKE '%'||ping_phrases.phrase||'%') LIMIT 1
    '''.format(in_text)).fetchone()

    if 1 in db_check:
        out_text = " ".join([ i for i in db.execute('''
            SELECT DISTINCT username FROM pingers WHERE "{0}" LIKE '%'||pingers.match||'%'
            '''.format(in_text)).fetchall() for i in i ])
        if 'EVERYONE GET IN HERE' in out_text:
            pingers_check = db.execute('''
                SELECT EXISTS(SELECT 1 FROM ping_exclude WHERE "{0}" LIKE '%'||ping_exclude.match||'%') LIMIT 1
                '''.format(in_text)).fetchone()
            if 1 in pingers_check:
                out_text = " ".join([ i for i in db.execute('''
                SELECT DISTINCT username FROM pingers WHERE "{0} {1}" NOT LIKE '%'||username||'%'
                '''.format(update.message.from_user.username, out_text)).fetchall() for i in i ])
            else:
                out_text = " ".join([ i for i in db.execute('''
                SELECT DISTINCT username FROM pingers WHERE pingers.username NOT LIKE "EVERYONE GET IN HERE" AND pingers.username NOT LIKE "{0}"
                '''.format(update.message.from_user.username)).fetchall() for i in i ])

    conn.commit()
    conn.close()

    if out_text:
        out_text = " ".join([ "@"+i for i in out_text.split(' ') ])
        bot.send_message( chat_id = update.message.chat_id, text = out_text )
        log_dict = {'timestamp': log_timestamp(), 
                      'pingers': pingers, 
                     'username': update.message.from_user.username }
        print("{timestamp}: ping {pingers} by @{username}".format(**log_dict))

#==== End of parser function ================================================

def log_timestamp():
    return(datetime.now(tzlocal()).strftime("[%d/%b/%Y:%H:%M:%S %z]"))

#============================================================================

print('{}: Started'.format(log_timestamp()))

updater    = Updater(token=BOT_TOKEN)
dispatcher = updater.dispatcher

dispatcher.add_handler(CommandHandler('start', start))
dispatcher.add_handler(CommandHandler('info', start))
dispatcher.add_handler(CommandHandler('weather', weather, pass_args=True))
dispatcher.add_handler(CommandHandler('w', weather, pass_args=True))
dispatcher.add_handler(CommandHandler('wset', wset, pass_args=True))
dispatcher.add_handler(CommandHandler('ibash', ibash, pass_args=True))
dispatcher.add_handler(CommandHandler('loglist', loglist, pass_args=True))
dispatcher.add_handler(MessageHandler(Filters.text, parser))

updater.start_polling()

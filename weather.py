import pyowm
from sqlalchemy.orm.exc import NoResultFound

from database import connector, Locations, ENGINE
from helpers import log_print
from tokens.tokens import ADMINS, WEATHER_TOKEN


def get_emoji(weather_status):
    emojis = {
        'Clouds': u'\U00002601',
        'Clear': u'\U00002600',
        'Rain': u'\U0001F327',
        'Extreme': u'\U0001F32A',
        'Snow': u'\U0001F328',
        'Thunderstorm': u'\U000026C8',
        'Mist': u'\U0001F32B',
        'Haze': u'\U0001F324',
        'notsure': u'\U0001F648'
    }

    return "".join([emojis[i] for i in emojis if weather_status == i])


def weather(bot, update, args):
    city = " ".join(args)
    username = update.message.from_user.username

    if not city:
        with connector(ENGINE) as ses:
            try:
                city = ses.query(Locations.city).filter(
                    Locations.username == username).one()
                city = "".join([i for i in city])
            except NoResultFound:
                try:
                    city = ses.query(Locations.city).filter(
                        Locations.username == "default_city").one()
                    city = "".join([i for i in city])
                except NoResultFound:
                    if username in ADMINS:
                        error_message = '''
                        You didn't set the default city
                        You can add default city by this command:
                        `/db insert into locations(username,city) \
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

    forecast = owm.three_hours_forecast(city)
    now_weather = observation.get_weather()
    city = observation.get_location().get_name()

    weathers = {}

    # Today
    today = pyowm.timeutils.next_three_hours()
    weather = forecast.get_weather_at(today)
    temp = str(round(weather.get_temperature(unit='celsius')["temp"]))
    if temp[0] != '-' and temp != "0":
        weathers["today", "temp", 0] = '+' + temp
    else:
        weathers["today", "temp", 0] = temp
    weathers["today", "emoji", 0] = get_emoji(weather.get_status())
    status = weather.get_detailed_status()
    weathers["today", "status", 0] = status[0].upper() + status[1:]

    # Tomorrow
    for i in [6, 12, 18]:
        weather = forecast.get_weather_at(pyowm.timeutils.tomorrow(i, 0))
        temp = str(round(weather.get_temperature('celsius')["temp"]))
        if temp[0] != '-' and temp != "0":
            weathers["tomorrow", "temp", i] = '+' + temp
        else:
            weathers["tomorrow", "temp", i] = temp
        weathers["tomorrow", "emoji", i] = get_emoji(weather.get_status())
        status = weather.get_detailed_status()
        weathers["tomorrow", "status", i] = status[0].upper() + status[1:]

    now_temp = str(round(now_weather.get_temperature(unit='celsius')["temp"]))
    if now_temp[0] != '-' and now_temp[0] != "0":
        now_temp = '+' + now_temp
    now_status = now_weather.get_detailed_status()
    now_status = now_status[0].upper() + now_status[1:]
    now_emoji = get_emoji(now_weather.get_status())

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


def wset(bot, update, args):
    city = " ".join(args)
    username = update.message.from_user.username

    with connector(ENGINE) as ses:
        try:
            ses.query(Locations.username).filter(
                Locations.username == username).one()
            if not city:
                w_city = "".join(ses.query(Locations.city).filter(
                    Locations.username == username).one())
                out_text = "@{0} city is {1}".format(username, w_city)
                city = 'deleted'
            elif city == "delete":
                ses.query(Locations.username).filter(
                    Locations.username == username).delete()
                out_text = "Deleted information about @{0}".format(username)
                city = 'deleted'
            else:
                ses.query(Locations).filter(
                    Locations.username == username).update({'city': city})
                out_text = "New city for @{0}: {1}".format(username, city)

        except NoResultFound:
            if not city or city == "delete":
                out_text = "Usage:\n/wset <city> - Set default city for /w\n/wset delete - Delete your default city".format(
                    username)
                city = 'none'
            else:
                new_location = Locations(
                    username=username,
                    city=city)
                ses.add(new_location)
                out_text = "Added @{0}: {1}".format(username, city)

    bot.send_message(chat_id=update.message.chat_id, text=out_text)
    log_print('Wset "{0}"'.format(out_text))
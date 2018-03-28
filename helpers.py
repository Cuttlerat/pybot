from datetime import datetime

from dateutil.tz import tzlocal


def start(bot, update):
    start_text = '''
    This is my first bot on Python.
    You can see the code here https://github.com/Cuttlerat/pybot
    by @Cuttlerat
    '''
    start_text = "\n".join([i.strip() for i in start_text.split('\n')])
    bot.send_message(chat_id=update.message.chat_id, text=start_text)


def bug(bot, update):
    bug_text = '''
    *Found a bug?*
    Please report it here: https://github.com/Cuttlerat/pybot/issues/new
    '''
    bug_text = "\n".join([i.strip() for i in bug_text.split('\n')])
    bot.send_message(chat_id=update.message.chat_id,
                     text=bug_text,
                     parse_mode='markdown')


def log_print(message, *username):
    timestamp = datetime.now(tzlocal()).strftime("[%d/%b/%Y:%H:%M:%S %z]")
    if username:
        print("{0}: {1} by @{2}".format(timestamp, message, "".join(username)))
    else:
        print("{0}: {1}".format(timestamp, message))
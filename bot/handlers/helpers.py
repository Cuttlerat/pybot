from telegram import InlineKeyboardMarkup

from bot.logger import log_print
from bot.handlers.random_content import random_content


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


def hat(bot, update):
    user_id = update.message.from_user.id
    faculties = ['Gryffindor', 'Slytherin', 'Hufflepuff', 'Ravenclaw']
    faculty = faculties[user_id % len(faculties)]

    bot.send_message(chat_id=update.message.chat_id,
                     text='*{0}*'.format(faculty),
                     reply_to_message_id=update.message.message_id,
                     parse_mode='markdown')
    log_print('Hat answer is {0} for user_id = {1}'.format(faculty, user_id))


def chat_id(bot, update):
    current_chat_id = update.message.chat_id
    username = update.message.from_user.username
    bot.send_message(chat_id=current_chat_id,
                     text="`{0}`".format(current_chat_id),
                     reply_to_message_id=update.message.message_id,
                     parse_mode='markdown')
    log_print('Chat id {0}'.format(current_chat_id), username)


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


def prepare_message(update):
    return update.message.text.lower().replace('ё', 'е').replace(',', '').replace('.', '')

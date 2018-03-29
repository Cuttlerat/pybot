import json

import requests
from bs4 import BeautifulSoup
from telegram import InlineKeyboardMarkup, InlineKeyboardButton

from logger import log_print


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
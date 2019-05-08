from services.crypto_compare import CryptoCompare
from logger import log_print
import requests
import json
from models.models import connector, ClashExclude, Pingers
from sqlalchemy import and_

def clash(config, bot, update):
    last_game={}
    username = update.message.from_user.username

    r = requests.post('https://www.codingame.com/services/ClashOfCodeRemoteService/createPrivateClash',
        headers={"content-type":"application/json;charset=UTF-8",
                 "cookie":"remcg={remcg};rememberMe={remember_me};cgSession={cg_session}".format(
                     remcg=config.clash_remcg(),
                     remember_me=config.clash_remember_me(),
                     cg_session=config.clash_cg_session())},
        data='[{}, {{"SHORT":true}}]'.format(config.clash_secret()))

    if r.status_code == 200:

        with connector(config.engine()) as ses:
            all_matches = ses.query(Pingers.username).filter(Pingers.chat_id == update.message.chat_id).order_by(Pingers.username).distinct().all()
            exclude = ses.query(ClashExclude.username).filter(ClashExclude.chat_id == update.message.chat_id).all()
            users = [ x for x in all_matches if x not in exclude ]
            users = [ x for x in users for x in x ]
            out_text = ""
        clash_id = json.loads(r.text)["success"]["publicHandle"]
        message = """
Please send /clash_disable if you don't want to be notified about new CoC games

https://www.codingame.com/clashofcode/clash/{clash_id}

{users}
        """.format(clash_id=clash_id, users=" ".join(["@{}".format(user) for user in users]))
        last_game["clash_id"] = clash_id
    else:
        clash_id = "Error"
        message = "Something went wrong..."

    sent = bot.send_message(chat_id=update.message.chat_id,
                     text=message)
    last_game["username"] = username
    last_game["message_id"] = sent.message_id

    with open("/tmp/clash_{}".format(update.message.chat_id), "w") as file:
        file.write(json.dumps(last_game)) 


    log_print('Clash of Code "{}"'.format(clash_id))


def clash_start(config, bot, update):

    username = update.message.from_user.username

    try:
        with open("/tmp/clash_{}".format(update.message.chat_id), "r") as file:
            last_game = json.loads(file.read())
    except IOError:
        last_game = {"clash_id":"", "message_id":"", "username": username}

    if last_game["clash_id"]:
        if last_game["username"] == username
            r = requests.post('https://www.codingame.com/services/ClashOfCodeRemoteService/startClashByHandle',
                headers={"content-type":"application/json;charset=UTF-8",
                         "cookie":"remcg={remcg};rememberMe={remember_me};cgSession={cg_session}".format(
                             remcg=config.clash_remcg(),
                             remember_me=config.clash_remember_me(),
                             cg_session=config.clash_cg_session())},
                data='[{clash_secret}, "{clash_id}"]'.format(clash_secret=config.clash_secret(),
                    clash_id=last_game["clash_id"]))

            if r.status_code == 200:
                message = 'CoC is about to start! Hurry up!'
            else:
                message = 'Could not start "{}" CoC game...'
        else:
            message = 'Only @{} is allowed to start the game'.format(username)
    else:
        last_game["clash_id"] = "None"
        message = "Could not find last CoC id"

    if last_game["message_id"]:
        bot.send_message(chat_id=update.message.chat_id,
                         reply_to_message_id=last_game["message_id"],
                         text=message,
                         parse_mode="markdown")
    else:
        bot.send_message(chat_id=update.message.chat_id,
                         text=message,
                         parse_mode="markdown")
    if last_game["clash_id"] != "None":
        log_print('Clash of Code "{}" started'.format(last_game["clash_id"]))


def clash_disable(config, bot, update):
    username = update.message.from_user.username
    chat_id = update.message.chat_id
    message_id = update.message.message_id
    if not username:
        msg = "You don't have username"
    else:
        with connector(config.engine()) as ses:
            all_excludes = ses.query(ClashExclude.username).filter(ClashExclude.chat_id == update.message.chat_id).all()
            all_excludes = [ x for x in all_excludes for x in x ]
            if username in all_excludes:
                msg = "You are already excluded"
            else:
                exclude = ClashExclude( 
                        username=username,
                        chat_id=chat_id)
                ses.add(exclude)
                msg = "You won't get any CoC notifications anymore. You can enable notifcations by /clash_enable"
    bot.send_message(chat_id=update.message.chat_id,
            reply_to_message_id=message_id,
            text=msg)
    log_print('Clash of Code enable', username)

def clash_enable(config, bot, update):
    username = update.message.from_user.username
    chat_id = update.message.chat_id
    message_id = update.message.message_id
    if not username:
        msg = "You don't have username"
    else:
        with connector(config.engine()) as ses:
            all_excludes = ses.query(ClashExclude.username).filter(ClashExclude.chat_id == update.message.chat_id).all()
            all_excludes = [ x for x in all_excludes for x in x ]
            if username in all_excludes:
                ses.query(ClashExclude).filter(and_(
                    ClashExclude.chat_id == chat_id,
                    ClashExclude.username == username)).delete()
                msg = "You will get CoC notifications now!"
            else:
                msg = "You are already excluded"
    bot.send_message(chat_id=update.message.chat_id,
            reply_to_message_id=message_id,
            text=msg,
            parse_mode="markdown")
    log_print('Clash of Code disable', username)

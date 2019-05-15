from logger import log_print
import requests
import json
from models.models import connector, ClashExclude, Pingers
from sqlalchemy import and_
import datetime
from tabulate import tabulate
from PIL import Image, ImageDraw, ImageFont
import io
import redis

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
        users=" ".join(["@{}".format(user) for user in users])
        message = """
Clash of Code!

https://www.codingame.com/clashofcode/clash/{clash_id}

{users}

Please send /clash_disable if you don't want to receive these notifications
        """.format(clash_id=clash_id, users=users)
        last_game["clash_id"] = clash_id
        log_print("Created",
                  chat_id=update.message.chat_id,
                  username=username,
                  clash_id=clash_id,
                  level="INFO",
                  command="clash")
    else:
        log_print("Failed on creating",
                  chat_id=update.message.chat_id,
                  username=username,
                  clash_id=clash_id,
                  level="ERROR",
                  command="clash")
        message = "Something went wrong..."

    sent = bot.send_message(chat_id=update.message.chat_id,
                     text=message)
    last_game["users"] = users
    last_game["username"] = username
    last_game["message_id"] = sent.message_id

    save_last_game(config, last_game, update.message.chat_id)


def save_last_game(config, last_game, chat_id):
    try:
        redis_db = redis.StrictRedis(host=config.redis_host, port=config.redis_port, db=config.redis_db)
        redis_db.set("clash_{}".format(chat_id), json.dumps(last_game))
        log_print("Saved to redis",
                  last_game=last_game,
                  key="clash_{}".format(chat_id),
                  level="DEBUG",
                  func="save_last_game")
    except redis.RedisError as e:
        log_print("Could not save last_game to redis",
                  error=str(e),
                  level="WARN",
                  command="clash")
        try:
            with open("/tmp/clash_{}".format(update.message.chat_id), "w") as file:
                file.write(json.dumps(last_game))
        except IOError as io_e:
            log_print("Could not save last_game to file",
                      error=str(io_e),
                      level="CRITICAL",
                      command="clash")
            raise

def get_last_game(config, chat_id):
    try:
        redis_db = redis.StrictRedis(host=config.redis_host, port=config.redis_port, db=config.redis_db)
        last_game = json.loads(redis_db.get("clash_{}".format(chat_id)))
        log_print("Read from redis",
                  last_game=last_game,
                  key="clash_{}".format(chat_id),
                  level="DEBUG",
                  func="save_last_game")
    except redis.RedisError as e:
        log_print("Could not read last_game from redis",
                  error=str(e),
                  level="WARN",
                  command="clash")
        try:
            with open("/tmp/clash_{}".format(update.message.chat_id), "r") as file:
                last_game = json.loads(file.read())
        except IOError:
            log_print("Could not read last_game from file",
                      error=str(io_e),
                      level="CRITICAL",
                      command="clash")
            last_game = {"clash_id":"", "message_id":"", "username": username}

    return last_game

def clash_start(config, bot, update):

    username = update.message.from_user.username

    last_game = get_last_game(config, update.message.chat_id)

    if last_game["clash_id"]:
        if last_game["username"] == username:
            r = requests.post('https://www.codingame.com/services/ClashOfCodeRemoteService/startClashByHandle',
                headers={"content-type":"application/json;charset=UTF-8",
                         "cookie":"remcg={remcg};rememberMe={remember_me};cgSession={cg_session}".format(
                             remcg=config.clash_remcg(),
                             remember_me=config.clash_remember_me(),
                             cg_session=config.clash_cg_session())},
                data='[{clash_secret}, "{clash_id}"]'.format(clash_secret=config.clash_secret(),
                    clash_id=last_game["clash_id"]))

            if r.status_code == 200:
                message="The game is about to start, hurry up!"
                if last_game["users"]:
                    message = '{users}\n\n{msg}'.format(
                        users=last_game["users"],
                        msg=message)
                log_print("Started",
                          chat_id=update.message.chat_id,
                          username=username,
                          clash_id=clash_id,
                          level="INFO",
                          command="clash_start")
            else:
                message = 'Could not start "{}" Clash game...'.format(
                    last_game["clash_id"])
                log_print("Failed on start",
                          chat_id=update.message.chat_id,
                          username=username,
                          clash_id=clash_id,
                          level="ERROR",
                          command="clash_start")
        else:
            last_game["message_id"] = update.message.message_id
            message = 'Only @{} is allowed to start the game'.format(last_game["username"])
    else:
        last_game["clash_id"] = "None"
        message = "Could not find the last Clash id"

    if last_game["message_id"]:
        bot.send_message(chat_id=update.message.chat_id,
                         reply_to_message_id=last_game["message_id"],
                         text=message,
                         parse_mode="markdown")
    else:
        bot.send_message(chat_id=update.message.chat_id,
                         text=message,
                         parse_mode="markdown")


def clash_disable(config, bot, update):
    username = update.message.from_user.username
    chat_id = update.message.chat_id
    message_id = update.message.message_id
    if not username:
        msg = "The unnamed ones are free from these silly humans vanity"
    else:
        with connector(config.engine()) as ses:
            all_excludes = ses.query(ClashExclude.username).filter(ClashExclude.chat_id == update.message.chat_id).all()
            all_excludes = [ x for x in all_excludes for x in x ]
            if username in all_excludes:
                msg = "You've already disabled notifications"
            else:
                exclude = ClashExclude(
                        username=username,
                        chat_id=chat_id)
                ses.add(exclude)
                msg = "Now you won't receive any notifications about Clash of Code games"
    bot.send_message(chat_id=update.message.chat_id,
            reply_to_message_id=message_id,
            text=msg)
    log_print("Disabled",
              chat_id=update.message.chat_id,
              username=username,
              clash_id=clash_id,
              level="INFO",
              command="clash_disable")

def clash_enable(config, bot, update):
    username = update.message.from_user.username
    chat_id = update.message.chat_id
    message_id = update.message.message_id
    if not username:
        msg = "The unnamed ones are free from these silly humans vanity"
    else:
        with connector(config.engine()) as ses:
            all_excludes = ses.query(ClashExclude.username).filter(ClashExclude.chat_id == update.message.chat_id).all()
            all_excludes = [ x for x in all_excludes for x in x ]
            if username in all_excludes:
                ses.query(ClashExclude).filter(and_(
                    ClashExclude.chat_id == chat_id,
                    ClashExclude.username == username)).delete()
                msg = "You will be notified when a new game is created!"
            else:
                msg = "You've already subscribed"
    bot.send_message(chat_id=update.message.chat_id,
            reply_to_message_id=message_id,
            text=msg,
            parse_mode="markdown")
    log_print("Enabled",
              chat_id=update.message.chat_id,
              username=username,
              clash_id=clash_id,
              level="INFO",
              command="clash_disable")

def clash_results_usage(config, bot, update):

    message="""
    I haven't found the last game, try to use it like this:
    ```
    /clash_results GAME_ID
    ```
    """
    message = "\n".join([i.strip() for i in message.split('\n')])
    bot.send_message(chat_id=update.message.chat_id,
                     text=message,
                     parse_mode="markdown")

def clash_results_to_byte_arr(message):

    font = ImageFont.truetype('/usr/share/fonts/Monospace.ttf', 48)
    img = Image.new('RGB', (100, 100), color = (50, 50, 50))
    d_temp = ImageDraw.Draw(img)
    text_size = d_temp.textsize(message, font)
    start_pos = (50, 20)
    text_size = (text_size[0]+start_pos[0]*2, text_size[1]+start_pos[1]*2)
    img = img.resize(text_size)
    d = ImageDraw.Draw(img)
    d.text(start_pos, message, font=font, fill=(240,240,240))

    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    return img_byte_arr

def clash_results(config, bot, update, args):

    username = update.message.from_user.username
    clash_ids = []
    results = {}

    if args:
        clash_ids = (list(set(args)))
    else:
        clash_ids = [get_last_game(config, update.message.chat_id)["clash_id"]]

    if not clash_ids:
        clash_results_usage(config, bot, update)
        return

    for clash_id in clash_ids:
        r = requests.post('https://www.codingame.com/services/ClashOfCodeRemoteService/findClashReportInfoByHandle',
                          headers={"content-type":"application/json;charset=UTF-8"},
                          data='[{}]'.format(clash_id))
        if r.status_code == 200:
            results = json.loads(r.text)
            if results["success"]:
                leaderboard = []
                clash_mode = results["success"]["mode"].capitalize() if "mode" in results["success"] else "Unknown"
                message = '''
                Game id: {clash_id}
                Game mode: {clash_mode}
                Status: {clash_status}

                '''.format(
                    clash_id=clash_id,
                    clash_mode=clash_mode,
                    clash_status="Finished" if results["success"]["finished"] else "In progress")
                if clash_mode != "Unknown":
                    headers=["", "Username", "Language", "Score", "Time"]
                    if clash_mode == "Shortest":
                        headers.append("Characters")
                    for player in results["success"]["players"]:
                        cache = []
                        cache.insert(0, player["rank"] if "rank" in player else 0)
                        cache.insert(1, player["codingamerNickname"] if "codingamerNickname" in player else "Unknown")
                        cache.insert(2, player["languageId"] if "languageId" in player else "Unknown")
                        cache.insert(3, '{}%'.format(player["score"] if "score" in player else "0"))
                        cache.insert(4, str(datetime.timedelta(milliseconds=player["duration"] if "duration" in player else 0)).split('.', 2)[0])
                        if clash_mode == "Shortest":
                            cache.insert(5, player["criterion"] if "criterion" in player else 0)

                        leaderboard.insert(player["rank"] if "rank" in player else 0, cache)

                    message += tabulate(sorted(leaderboard),
                                        headers,
                                        tablefmt='psql')
                message += "\n"
                message = "\n".join([i.strip() for i in message.split('\n')])

                img_byte_arr = clash_results_to_byte_arr(message)

                bot.sendPhoto(chat_id=update.message.chat_id,
                              photo=io.BufferedReader(img_byte_arr),
                              caption='https://www.codingame.com/clashofcode/clash/report/{}'.format(
                                       clash_id))

    log_print("Results",
              chat_id=update.message.chat_id,
              username=username,
              clash_id=clash_id,
              level="INFO",
              command="clash_results")

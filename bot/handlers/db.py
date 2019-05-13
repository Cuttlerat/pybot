from sqlalchemy import create_engine
from sqlalchemy.exc import ResourceClosedError

from logger import log_print


def database_handler(config, bot, update, args):
    if update.message.from_user.username not in config.admins():
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

        engine = create_engine(config.database())
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
        log_print(command, 
                  username=update.message.from_user.username,
                  chat_id=update.message.chat_id,
                  level="INFO",
                  command="db")

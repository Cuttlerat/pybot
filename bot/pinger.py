import re

from sqlalchemy import and_

from bot.logger import log_print
from bot.models import connector, ENGINE, Pingers
from bot.tokens.tokens import ADMINS


def pinger(bot, update, args):
    chat_id = update.message.chat_id
    username = update.message.from_user.username
    args_line = " ".join(args)

    if username in ADMINS:
        try:
            p_username = re.sub('[@]', '', args[0])
            try:
                match = args[1].lower()
            except:
                if args[0] not in ["show", "all", "delete"]:
                    p_username = username
                    match = args[0]
            if not p_username: raise Exception
        except:
            usage_text = "Usage: \n`/ping username <word>`\n`/ping show <username>`\n`/ping all`\n`/ping delete username <word>`"
            bot.send_message(chat_id=update.message.chat_id,
                             parse_mode='markdown',
                             text=usage_text)
            return
        with connector(ENGINE) as ses:
            try:
                if p_username == "all":
                    all_matches = ses.query(Pingers).filter(Pingers.chat_id == chat_id).all()
                    out_text = ""
                    for match in all_matches:
                        out_text += "\n{}".format(match.match)
                    bot.send_message(chat_id=update.message.chat_id,
                                     text=out_text)
                elif p_username == "show":
                    try:
                        username_show = re.sub('[@]', '', args[1])
                    except:
                        out_text = "Usage `/ping show <username>`"
                        bot.send_message(chat_id=update.message.chat_id,
                                         parse_mode='markdown',
                                         text=out_text)
                        return
                    try:
                        user_matches = ses.query(Pingers).filter(Pingers.chat_id == chat_id,
                                                                 Pingers.username == username_show).all()
                        out_text = ""
                        for match in user_matches:
                            out_text += "\n{}".format(match.match)
                        if out_text == "":
                            out_text = "No such user"
                        bot.send_message(chat_id=update.message.chat_id,
                                         text=out_text)
                        log_print('Show pings of "{0}", by {1}'.format(username_show, username))
                    except:
                        bot.send_message(chat_id=update.message.chat_id,
                                         text="There was some trouble")
                        log_print('There was some trouble in pinger function by "{0}"'.format(args_line), username)
                elif p_username == "delete":
                    try:
                        p_username = re.sub('[@]', '', args[1])
                        try:
                            delete_match = args[2].lower()

                        except:
                            p_username = username
                            delete_match = args[1].lower()
                    except:
                        out_text = "Usage `/ping delete username <word>`"
                        bot.send_message(chat_id=update.message.chat_id,
                                         parse_mode='markdown',
                                         text=out_text)
                        return
                    if delete_match == "all":
                        ses.query(Pingers).filter(and_(
                            Pingers.chat_id == chat_id,
                            Pingers.username == p_username)).delete()
                        bot.send_message(chat_id=update.message.chat_id,
                                         text="Deleted all matches for user @{}".format(p_username))
                    else:
                        ses.query(Pingers).filter(and_(
                            Pingers.chat_id == chat_id,
                            Pingers.username == p_username,
                            Pingers.match == delete_match)).delete()
                        bot.send_message(chat_id=update.message.chat_id,
                                         text="Deleted")
                    log_print('Delete pinger "{0}" by @{1}'.format(args_line, username))
                else:
                    with connector(ENGINE) as ses:
                        new_pinger = Pingers(
                            username=p_username,
                            match=match,
                            chat_id=chat_id)
                        ses.add(new_pinger)
                    bot.send_message(chat_id=update.message.chat_id,
                                     text="Successfuly added ping for {0} with match {1}".format(p_username, match))
                    log_print('Added pinger "{0}"'.format(args_line), username)
            except:
                bot.send_message(chat_id=update.message.chat_id,
                                 text="There was some trouble")
                log_print('There was some trouble in pinger function by "{0}"'.format(args_line), username)
    else:
        try:
            try:
                user_match = args[0].lower()
                if not user_match: raise Exception
            except:
                out_text = "Usage: \n`/ping <word>`\n`/ping show <username>`\n`/ping me`\n`/ping delete <word>`"
                bot.send_message(chat_id=update.message.chat_id,
                                 parse_mode='markdown',
                                 text=out_text)
                return
            with connector(ENGINE) as ses:
                if user_match == "me":
                    all_matches = ses.query(Pingers).filter(and_(
                        Pingers.chat_id == chat_id,
                        Pingers.username == username)).all()
                    out_text = ""
                    for match in all_matches:
                        out_text += "\n{}".format(match.match)
                    bot.send_message(chat_id=update.message.chat_id,
                                     text=out_text)
                elif user_match == "show":
                    try:
                        username_show = re.sub('[@]', '', args[1])
                    except:
                        out_text = "Usage `/ping show <username>`"
                        bot.send_message(chat_id=update.message.chat_id,
                                         parse_mode='markdown',
                                         text=out_text)
                        return
                    try:
                        user_matches = ses.query(Pingers).filter(Pingers.chat_id == chat_id,
                                                                 Pingers.username == username_show).all()
                        out_text = ""
                        for match in user_matches:
                            out_text += "\n{}".format(match.match)
                        if out_text == "":
                            out_text = "No such user"
                        bot.send_message(chat_id=update.message.chat_id,
                                         text=out_text)
                        log_print('Show pings of "{0}", by {1}'.format(username_show, username))
                    except:
                        bot.send_message(chat_id=update.message.chat_id,
                                         text="There was some trouble")
                        log_print('There was some trouble in pinger function by "{0}"'.format(args_line), username)
                elif user_match == "delete":
                    try:
                        delete_match = args[1].lower()
                    except:
                        out_text = "Usage `/ping delete <word>`"
                        bot.send_message(chat_id=update.message.chat_id,
                                         parse_mode='markdown',
                                         text=out_text)
                        return
                    ses.query(Pingers).filter(and_(
                        Pingers.chat_id == chat_id,
                        Pingers.username == username,
                        Pingers.match == delete_match)).delete()
                    bot.send_message(chat_id=update.message.chat_id,
                                     text="Deleted")
                    log_print('Delete pinger "{0}"'.format(args_line))

                else:
                    count = ses.query(Pingers).filter(and_(
                        Pingers.chat_id == chat_id,
                        Pingers.username == username)).count()
                    if count < 10:
                        new_pinger = Pingers(
                            username=username,
                            match=user_match,
                            chat_id=chat_id)
                        ses.add(new_pinger)
                        bot.send_message(chat_id=update.message.chat_id,
                                         text="Successfuly added ping for {0} with match {1}".format(username,
                                                                                                     user_match))
                        log_print('Added pinger "{0}"'.format(args_line), username)
                    else:
                        bot.send_message(chat_id=update.message.chat_id,
                                         text="You can add only 10 matches")
                        log_print('Pinger limit is settled', username)
        except:
            bot.send_message(chat_id=update.message.chat_id,
                             text="There was some trouble")
            log_print('Error while add pinger "{0}"'.format(args_line), username)
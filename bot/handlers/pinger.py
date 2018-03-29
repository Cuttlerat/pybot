import re

from sqlalchemy import and_

from logger import log_print
from data.models import connector, ENGINE, Pingers
from tokens.tokens import ADMINS


def pinger_handler(bot, update, args):
    username = update.message.from_user.username
    pinger = PingerCommand(bot, update, args)
    if username in ADMINS:
        pinger.ping_from_admin()
    else:
        pinger.ping_from_user()


class PingerCommand:
    def __init__(self, bot, update, args):
        self.args = args
        self.update = update
        self.bot = bot

        self.args_line = " ".join(args)
        self.chat_id = update.message.chat_id
        self.username = update.message.from_user.username

    def ping_from_admin(self):
        try:
            ping_username = re.sub('[@]', '', self.args[0])
            try:
                match = self.args[1].lower()
            except:
                if self.args[0] not in ["show", "all", "delete"]:
                    ping_username = self.username
                    match = self.args[0]
            if not ping_username:
                raise Exception
        except:
            usage_text = "Usage: \n`/ping username <word>`\n`/ping show <username>`\n`/ping all`\n`/ping delete " \
                         "username <word>` "
            self.bot.send_message(chat_id=self.update.message.chat_id,
                                  parse_mode='markdown',
                                  text=usage_text)
            return

        with connector(ENGINE) as ses:
            try:
                if ping_username == "all":
                    self.__answer_for_all(ses)
                elif ping_username == "show":
                    self.__answer_for_show(ses)
                elif ping_username == "delete":
                    self.__answer_for_delete_from_admin(ses)
                else:
                    with connector(ENGINE) as inner_ses:
                        new_pinger = Pingers(
                            username=ping_username,
                            match=match,
                            chat_id=self.chat_id)
                        inner_ses.add(new_pinger)
                    self.bot.send_message(chat_id=self.update.message.chat_id,
                                          text="Successfully added ping for '{0}' with match '{1}'".format(ping_username,
                                                                                                          match))
                    log_print('Added pinger "{0}"'.format(self.args_line), self.username)
            except:
                self.bot.send_message(chat_id=self.update.message.chat_id,
                                      text="There was some trouble")
                log_print('There was some trouble in pinger function by "{0}"'.format(self.args_line), self.username)

    def ping_from_user(self):
        try:
            try:
                user_match = self.args[0].lower()
                if not user_match:
                    raise Exception
            except:
                out_text = "Usage: \n`/ping <word>`\n`/ping show <username>`\n`/ping me`\n`/ping delete <word>`"
                self.bot.send_message(chat_id=self.update.message.chat_id,
                                      parse_mode='markdown',
                                      text=out_text)
                return
            with connector(ENGINE) as ses:
                if user_match == "me":
                    self.__answer_for_me(ses)
                elif user_match == "show":
                    self.__answer_for_show(ses)
                elif user_match == "delete":
                    self.__answer_for_delete(ses)
                else:
                    count = ses.query(Pingers).filter(and_(
                        Pingers.chat_id == self.chat_id,
                        Pingers.username == self.username)).count()
                    if count < 10:
                        new_pinger = Pingers(
                            username=self.username,
                            match=user_match,
                            chat_id=self.chat_id)
                        ses.add(new_pinger)
                        self.bot.send_message(chat_id=self.update.message.chat_id,
                                              text="Successfully added ping for {0} with match {1}".format(
                                                  self.username,
                                                  user_match))
                        log_print('Added pinger "{0}"'.format(self.args_line), self.username)
                    else:
                        self.bot.send_message(chat_id=self.update.message.chat_id,
                                              text="You can add only 10 matches")
                        log_print('Pinger limit is settled', self.username)
        except:
            self.bot.send_message(chat_id=self.update.message.chat_id,
                                  text="There was some trouble")
            log_print('Error while add pinger "{0}"'.format(self.args_line), self.username)

    def __answer_for_all(self, ses):
        all_matches = ses.query(Pingers).filter(Pingers.chat_id == self.chat_id).all()
        out_text = ""
        for match in all_matches:
            out_text += "\n{}".format(match.match)
        self.bot.send_message(chat_id=self.update.message.chat_id,
                              text=out_text)

    def __answer_for_show(self, ses):
        try:
            username_show = re.sub('[@]', '', self.args[1])
        except:
            out_text = "Usage `/ping show <username>`"
            self.bot.send_message(chat_id=self.update.message.chat_id,
                                  parse_mode='markdown',
                                  text=out_text)
            return
        try:
            user_matches = ses.query(Pingers).filter(Pingers.chat_id == self.chat_id,
                                                     Pingers.username == username_show).all()
            out_text = ""
            for match in user_matches:
                out_text += "\n{}".format(match.match)
            if out_text == "":
                out_text = "No such user"
            self.bot.send_message(chat_id=self.update.message.chat_id,
                                  text=out_text)
            log_print('Show pings of "{0}", by {1}'.format(username_show, self.username))
        except:
            self.bot.send_message(chat_id=self.update.message.chat_id,
                                  text="There was some trouble")
            log_print('There was some trouble in pinger function by "{0}"'.format(self.args_line),
                      self.username)

    def __answer_for_delete_from_admin(self, ses):
        try:
            p_username = re.sub('[@]', '', self.args[1])
            try:
                delete_match = self.args[2].lower()

            except:
                p_username = self.username
                delete_match = self.args[1].lower()
        except:
            out_text = "Usage `/ping delete username <word>`"
            self.bot.send_message(chat_id=self.update.message.chat_id,
                                  parse_mode='markdown',
                                  text=out_text)
            return
        if delete_match == "all":
            ses.query(Pingers).filter(and_(
                Pingers.chat_id == self.chat_id,
                Pingers.username == p_username)).delete()
            self.bot.send_message(chat_id=self.update.message.chat_id,
                                  text="Deleted all matches for user @{}".format(p_username))
        else:
            ses.query(Pingers).filter(and_(
                Pingers.chat_id == self.chat_id,
                Pingers.username == p_username,
                Pingers.match == delete_match)).delete()
            self.bot.send_message(chat_id=self.update.message.chat_id,
                                  text="Deleted")
        log_print('Delete pinger "{0}" by @{1}'.format(self.args_line, self.username))

    def __answer_for_delete(self, ses):
        try:
            delete_match = self.args[1].lower()
        except:
            out_text = "Usage `/ping delete <word>`"
            self.bot.send_message(chat_id=self.update.message.chat_id,
                                  parse_mode='markdown',
                                  text=out_text)
            return
        ses.query(Pingers).filter(and_(
            Pingers.chat_id == self.chat_id,
            Pingers.username == self.username,
            Pingers.match == delete_match)).delete()
        self.bot.send_message(chat_id=self.update.message.chat_id,
                              text="Deleted")
        log_print('Delete pinger "{0}"'.format(self.args_line))

    def __answer_for_me(self, ses):
        all_matches = ses.query(Pingers).filter(and_(
            Pingers.chat_id == self.chat_id,
            Pingers.username == self.username)).all()
        out_text = ""
        for match in all_matches:
            out_text += "\n{}".format(match.match)
        self.bot.send_message(chat_id=self.update.message.chat_id,
                              text=out_text)

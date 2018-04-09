import re

from sqlalchemy import and_

from logger import log_print
from models.models import connector, Pingers


def pinger(config, bot, update, args):
    username = update.message.from_user.username
    pinger_command = PingerCommand(config, bot, update, args)
    if username in config.admins():
        pinger_command.ping_from_admin()
    else:
        pinger_command.ping_from_user()


class PingerCommand:
    def __init__(self, config, bot, update, args):
        self.args = args
        self.update = update
        self.bot = bot
        self.config = config

        self.args_line = " ".join(args)
        self.chat_id = update.message.chat_id
        self.username = update.message.from_user.username

    def ping_from_admin(self):
        try:
            ping_usernames = [ re.sub('[@]', '', i) for i in self.args if "@" == i[0] ]
            command = self.args[0]
            if "@" != self.args[-1][0]:
                match = self.args[-1].lower()
            if not ping_usernames:
                ping_usernames = [self.username]
                
            if not match and not command:
                raise Exception
        except:
            usage_text = "Usage: \n`/ping @username <word>`\n`/ping show @username`\n`/ping all`\n`/ping delete " \
                         "@username <word>` "
            self.bot.send_message(chat_id=self.update.message.chat_id,
                                  parse_mode='markdown',
                                  text=usage_text)
            return

        with connector(self.config.engine()) as ses:
            try:
                if command == "all":
                    self.__answer_for_all(ses)
                elif command == "show":
                    self.__answer_for_show(ses)
                elif command == "delete":
                    self.__answer_for_delete_from_admin(ses)
                else:
                    for ping_username in ping_usernames:
                        with connector(self.config.engine()) as inner_ses:
                            new_pinger = Pingers(
                                username=ping_username,
                                match=match,
                                chat_id=self.chat_id)
                            inner_ses.add(new_pinger)
                        self.bot.send_message(chat_id=self.update.message.chat_id,
                                          text="Successfully added ping for @{0} with match '{1}'".format(
                                              ping_username,
                                              match))
                        log_print('Added pinger @{0} with match "{1}"'.format(ping_username, match), self.username)
            except:
                self.bot.send_message(chat_id=self.update.message.chat_id,
                                      text="There was some trouble")
                log_print('There was some trouble in pinger function by "{0}"'.format(self.args_line), self.username)

    def ping_from_user(self):
        try:
            try:
                user_match = self.args[-1].lower()
                if not user_match:
                    raise Exception
            except:
                out_text = "Usage: \n`/ping <word>`\n`/ping show @username`\n`/ping me`\n`/ping delete <word>`"
                self.bot.send_message(chat_id=self.update.message.chat_id,
                                      parse_mode='markdown',
                                      text=out_text)
                return
            with connector(self.config.engine()) as ses:
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
            out_text += "\n@{0} | {1}".format(match.username, match.match)
        self.bot.send_message(chat_id=self.update.message.chat_id,
                              text=out_text)

    def __answer_for_show(self, ses):
        try:
            username_show = re.sub('[@]', '', self.args[1])
        except:
            out_text = "Usage `/ping show @username`"
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
            p_usernames = [re.sub('[@]', '', i) for i in self.args if "@" == i[0]]
            if "@" != self.args[-1][0]:
                delete_match = self.args[-1].lower()
            if not p_usernames:
                p_usernames = [self.username]
        except:
            out_text = "Usage `/ping delete @username <word>`"
            self.bot.send_message(chat_id=self.update.message.chat_id,
                                  parse_mode='markdown',
                                  text=out_text)
            return
        for p_username in p_usernames:
            if delete_match == "all":
                ses.query(Pingers).filter(and_(
                    Pingers.chat_id == self.chat_id,
                    Pingers.username == p_username)).delete()
                self.bot.send_message(chat_id=self.update.message.chat_id,
                                      text="Deleted all matches for user @{}".format(p_username))
                log_print('Delete all matches for pinger @{0} by @{1}'.format(p_username, self.username))
            else:
                ses.query(Pingers).filter(and_(
                    Pingers.chat_id == self.chat_id,
                    Pingers.username == p_username,
                    Pingers.match == delete_match)).delete()
                self.bot.send_message(chat_id=self.update.message.chat_id,
                                      text="Deleted match '{0}' for user @{1}".format(delete_match, p_username))
                log_print('Delete match "{0}" for pinger @{1} by @{2}'.format(delete_match, p_username, self.username))

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

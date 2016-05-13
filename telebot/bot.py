import ConfigParser
from zabbix.zabbix import Zabbix
import telegram
from telegram.ext import Updater, CommandHandler
import pdb


class TelegramBot(object):

    def __init__(self):
        self.zabb = Zabbix()
        self.__get_config()

        self.__updater = Updater(self.telegram_key)

        self.__updater.dispatcher.addHandler(
            CommandHandler('start', self.start))

        self.__updater.dispatcher.addHandler(
            CommandHandler('hello', self.hello))

        self.__updater.dispatcher.addHandler(
            CommandHandler('hostgroups', self.hostgroups))

        self.__updater.dispatcher.addHandler(
            CommandHandler('hosts', self.hosts, pass_args=True))

        self.__updater.start_polling()
        self.__updater.idle()

    def __get_config(self):
        self.config = ConfigParser.ConfigParser()
        self.config.read('prod.cfg')

        self.telegram_key = self.config.get('TELEGRAM', 'KEY')

    def start(self, bot, update):
        bot.sendMessage(update.message.chat_id, text='Hello World!')

    def hello(self, bot, update):
        bot.sendChatAction(chat_id=update.message.chat_id,
                           action=telegram.ChatAction.TYPING)
        bot.sendMessage(update.message.chat_id,
                        text='Hello {0}'
                        .format(update.message.from_user.first_name))

    def hostgroups(self, bot, update):
        bot.sendChatAction(chat_id=update.message.chat_id,
                           action=telegram.ChatAction.TYPING)
        bot.sendMessage(update.message.chat_id,
                        text=self.zabb.get_hostgroups())

    def hosts(self, bot, update, args):
        bot.sendChatAction(chat_id=update.message.chat_id,
                           action=telegram.ChatAction.TYPING)
        for host in self.zabb.get_hosts_by_hostgroup(args):
            bot.sendMessage(update.message.chat_id,
                            text=host)

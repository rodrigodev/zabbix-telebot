import ConfigParser
from zabbix.zabbix import Zabbix

from telegram.ext import Updater, CommandHandler


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

        self.__updater.start_polling()
        self.__updater.idle()

    def __get_config(self):
        self.config = ConfigParser.ConfigParser()
        self.config.read('prod.cfg')

        self.telegram_key = self.config.get('TELEGRAM', 'KEY')

    def start(self, bot, update):
        bot.sendMessage(update.message.chat_id, text='Hello World!')

    def hello(self, bot, update):
        bot.sendMessage(update.message.chat_id,
                        text='Hello {0}'
                        .format(update.message.from_user.first_name))

    def hostgroups(self, bot, update):
        bot.sendMessage(update.message.chat_id,
                        text=self.zabb.get_hostgroups())

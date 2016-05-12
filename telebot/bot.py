import ConfigParser
from telegram.ext import Updater, CommandHandler

config = ConfigParser.ConfigParser()
config.read('prod.cfg')

telegram_key = config.get('TELEGRAM', 'KEY')

def start(bot, update):
    bot.sendMessage(update.message.chat_id, text='Hello World!')

def hello(bot, update):
    bot.sendMessage(update.message.chat_id,
                        text='Hello {0}'.format(update.message.from_user.first_name))

class TelegramBot(object):
    def __init__(self):
        self.__updater = Updater(telegram_key)
        self.__updater.dispatcher.addHandler(CommandHandler('start', start))
        self.__updater.dispatcher.addHandler(CommandHandler('hello', hello))
        self.__updater.start_polling()
        self.__updater.idle()

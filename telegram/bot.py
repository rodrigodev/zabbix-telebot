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

updater = Updater(telegram_key)

updater.dispatcher.addHandler(CommandHandler('start', start))
updater.dispatcher.addHandler(CommandHandler('hello', hello))

updater.start_polling()
updater.idle()
